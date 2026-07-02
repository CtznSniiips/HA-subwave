"""Media player entity for SUB/WAVE."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.components.media_player import (
    BrowseError,
    BrowseMedia,
    MediaClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, STREAM_FORMATS
from .coordinator import SubWaveCoordinator
from .entity import SubWaveEntity
from .http import get_proxy_stream_url

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.BROWSE_MEDIA | MediaPlayerEntityFeature.PLAY_MEDIA
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SubWaveCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SubWaveMediaPlayer(coordinator, entry.entry_id)])


class SubWaveMediaPlayer(SubWaveEntity, MediaPlayerEntity):
    """Represents the SUB/WAVE live stream as a browsable media source.

    This entity does not play audio on the Home Assistant host itself -
    there's no local speaker to control. Instead it surfaces now-playing
    metadata (title/artist/DJ/etc) and exposes browse_media so the stream
    URL can be sent to a real player (Sonos, cast, etc) via
    media_player.play_media in an automation/script.
    """

    _attr_name = None
    _attr_supported_features = SUPPORTED_FEATURES
    _attr_media_content_type = MediaType.MUSIC

    def __init__(self, coordinator: SubWaveCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_media_player"

    @property
    def state(self) -> MediaPlayerState:
        data = self.coordinator.data or {}
        if not data.get("streamOnline"):
            return MediaPlayerState.OFF
        listeners = (data.get("listeners") or {}).get("current", 0)
        return MediaPlayerState.PLAYING if listeners else MediaPlayerState.IDLE

    @property
    def media_title(self) -> str | None:
        return (self.coordinator.data or {}).get("nowPlaying", {}).get("title")

    @property
    def media_artist(self) -> str | None:
        return (self.coordinator.data or {}).get("nowPlaying", {}).get("artist")

    @property
    def media_album_name(self) -> str | None:
        return (self.coordinator.data or {}).get("nowPlaying", {}).get("album")

    def _cover_art_url(self) -> str | None:
        """Direct (LAN-only) URL for the current track's cover art, if any."""
        data = self.coordinator.data or {}
        subsonic_id = (data.get("nowPlaying") or {}).get("subsonic_id")
        if subsonic_id:
            return self.coordinator.cover_url(subsonic_id)
        avatar = (data.get("dj") or {}).get("avatar")
        return f"{self.coordinator.base_url}{avatar}" if avatar else None

    @property
    def media_image_hash(self) -> str | None:
        """Cache-busting key so the picture updates when the track changes.

        Home Assistant only re-fetches media_image bytes when this value
        changes, so keying it off subsonic_id (falling back to the DJ
        avatar path) makes sure the artwork updates every new track.
        """
        data = self.coordinator.data or {}
        subsonic_id = (data.get("nowPlaying") or {}).get("subsonic_id")
        if subsonic_id:
            return subsonic_id
        return (data.get("dj") or {}).get("avatar")

    async def async_get_media_image(self) -> tuple[bytes | None, str | None]:
        """Fetch cover art bytes so HA can serve/cache them itself.

        media_image_remotely_accessible defaults to False, so returning
        bytes here (instead of a URL via media_image_url) makes Home
        Assistant proxy the artwork through its own authenticated
        /api/media_player_proxy endpoint - meaning it works through Nabu
        Casa or a reverse proxy the same way the audio stream proxy does,
        with no extra setup.
        """
        url = self._cover_art_url()
        if url is None:
            return None, None

        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(10):
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return None, None
                    return await resp.read(), resp.headers.get("Content-Type")
        except (aiohttp.ClientError, asyncio.TimeoutError):
            _LOGGER.debug("Failed to fetch SUB/WAVE artwork from %s", url)
            return None, None

    @property
    def app_name(self) -> str | None:
        dj = (self.coordinator.data or {}).get("dj") or {}
        return dj.get("station")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        dj = data.get("dj") or {}
        context = data.get("context") or {}
        now_playing = data.get("nowPlaying") or {}
        stream = data.get("stream") or {}
        weather = context.get("weather") or {}
        time_ctx = context.get("time") or {}
        listeners = data.get("listeners") or {}
        queue_state = data.get("queueState") or {}
        current = queue_state.get("current") or {}
        upcoming = queue_state.get("upcoming") or []
        return {
            "stream_url": self.coordinator.stream_url("mp3"),
            "proxy_stream_url": get_proxy_stream_url(self.hass, self._entry_id, "mp3"),
            "cover_art_url": self._cover_art_url(),
            "requests_endpoint": f"subwave/{self._entry_id}/requests",
            "requested_by": current.get("requestedBy"),
            "source": current.get("source"),
            "up_next": upcoming[0].get("title") if upcoming else None,
            "queue_length": len(upcoming),
            "dj_name": dj.get("name"),
            "dj_tagline": dj.get("tagline"),
            "genre": now_playing.get("genre"),
            "moods": now_playing.get("moods"),
            "energy": now_playing.get("energy"),
            "year": now_playing.get("year"),
            "weather_condition": weather.get("condition"),
            "weather_temp": weather.get("temp"),
            "location": weather.get("location"),
            "show": time_ctx.get("show"),
            "vibe": time_ctx.get("vibe"),
            "stream_bitrate": stream.get("bitrate"),
            "stream_format": stream.get("format"),
            "listeners_current": listeners.get("current"),
            "listeners_peak": listeners.get("peak"),
        }

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        """No local playback happens here; SUB/WAVE is a live stream source.

        Use async_browse_media to pick a stream URL, then call
        media_player.play_media on the *target* speaker with that URL.
        """
        return

    def _enabled_formats(self) -> list[str]:
        stream = (self.coordinator.data or {}).get("stream") or {}
        formats = ["mp3"]
        if stream.get("opusEnabled"):
            formats.append("opus")
        if stream.get("flacEnabled"):
            formats.append("flac")
        if stream.get("aacEnabled"):
            formats.append("aac")
        return [fmt for fmt in formats if fmt in STREAM_FORMATS]

    def _station_name(self) -> str:
        return (self.coordinator.data or {}).get("dj", {}).get("station", "SUB/WAVE")

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        station_name = self._station_name()
        enabled_formats = self._enabled_formats()

        # Root: choose between a direct LAN URL (fastest, only reachable on
        # your local network) and a URL proxied through Home Assistant
        # itself (works anywhere HA is reachable - Nabu Casa, reverse
        # proxy, etc - since it's just HA's own webserver relaying bytes).
        if media_content_id in (None, "", "subwave://root"):
            return BrowseMedia(
                title=station_name,
                media_class=MediaClass.DIRECTORY,
                media_content_id="subwave://root",
                media_content_type=MediaType.MUSIC,
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMedia(
                        title="Direct stream (same network)",
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="subwave://direct",
                        media_content_type=MediaType.MUSIC,
                        can_play=False,
                        can_expand=True,
                    ),
                    BrowseMedia(
                        title="Via Home Assistant (remote-accessible)",
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="subwave://proxy",
                        media_content_type=MediaType.MUSIC,
                        can_play=False,
                        can_expand=True,
                    ),
                ],
            )

        if media_content_id == "subwave://direct":
            children = [
                BrowseMedia(
                    title=f"{station_name} ({fmt.upper()})",
                    media_class=MediaClass.MUSIC,
                    media_content_id=self.coordinator.stream_url(fmt),
                    media_content_type=MediaType.MUSIC,
                    can_play=True,
                    can_expand=False,
                )
                for fmt in enabled_formats
            ]
            return BrowseMedia(
                title="Direct stream (same network)",
                media_class=MediaClass.DIRECTORY,
                media_content_id="subwave://direct",
                media_content_type=MediaType.MUSIC,
                can_play=False,
                can_expand=True,
                children=children,
            )

        if media_content_id == "subwave://proxy":
            children = []
            for fmt in enabled_formats:
                url = get_proxy_stream_url(self.hass, self._entry_id, fmt)
                if url is None:
                    continue
                children.append(
                    BrowseMedia(
                        title=f"{station_name} ({fmt.upper()}, via HA)",
                        media_class=MediaClass.MUSIC,
                        media_content_id=url,
                        media_content_type=MediaType.MUSIC,
                        can_play=True,
                        can_expand=False,
                    )
                )
            return BrowseMedia(
                title="Via Home Assistant (remote-accessible)",
                media_class=MediaClass.DIRECTORY,
                media_content_id="subwave://proxy",
                media_content_type=MediaType.MUSIC,
                can_play=False,
                can_expand=True,
                children=children,
            )

        raise BrowseError(f"Media not found: {media_content_id}")
