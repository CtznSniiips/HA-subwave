"""Data update coordinator for SUB/WAVE."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_HEALTH, API_NOW_PLAYING, API_REQUESTS, API_SESSION, API_STATE, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SubWaveCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the SUB/WAVE now-playing API."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        scan_interval: int,
    ) -> None:
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def now_playing_url(self) -> str:
        """Full URL of the now-playing endpoint."""
        return f"{self.base_url}{API_NOW_PLAYING}"

    @property
    def state_url(self) -> str:
        """Full URL of the richer state endpoint (queue, history, DJ log)."""
        return f"{self.base_url}{API_STATE}"

    @property
    def session_url(self) -> str:
        """Full URL of the session transcript endpoint (DJ commentary, scenario shifts)."""
        return f"{self.base_url}{API_SESSION}"

    @property
    def requests_url(self) -> str:
        """Full URL of the listener-requests endpoint."""
        return f"{self.base_url}{API_REQUESTS}"

    @property
    def health_url(self) -> str:
        """Full URL of the lightweight health-check endpoint."""
        return f"{self.base_url}{API_HEALTH}"

    def stream_url(self, fmt: str = "mp3") -> str:
        """Return the stream URL for a given format (mp3/opus/flac/aac)."""
        return f"{self.base_url}/stream.{fmt}"

    def cover_url(self, subsonic_id: str) -> str:
        """Return the album art URL for a track's subsonic_id."""
        return f"{self.base_url}/api/cover/{subsonic_id}"

    async def _async_update_data(self) -> dict[str, Any]:
        # now-playing is the primary payload - a failure here fails the update.
        try:
            async with asyncio.timeout(10):
                async with self._session.get(self.now_playing_url) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(
                f"Error communicating with SUB/WAVE at {self.base_url}: {err}"
            ) from err
        except asyncio.TimeoutError as err:
            raise UpdateFailed(
                f"Timed out communicating with SUB/WAVE at {self.base_url}"
            ) from err

        # /api/state (queue, history, dj log), /api/session (DJ commentary,
        # scenario/mood shifts), and /api/health (broadcast status) are all
        # supplementary - older SUB/WAVE versions may not have them, so
        # don't fail the whole update if any is unreachable; just leave
        # that key empty.
        queue_state, session_log, health = await asyncio.gather(
            self._async_fetch_json(self.state_url),
            self._async_fetch_json(self.session_url),
            self._async_fetch_json(self.health_url),
        )
        data["queueState"] = queue_state
        data["sessionLog"] = session_log
        data["health"] = health
        return data

    async def _async_fetch_json(self, url: str) -> dict[str, Any]:
        try:
            async with asyncio.timeout(10):
                async with self._session.get(url) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Could not fetch SUB/WAVE %s: %s", url, err)
            return {}
