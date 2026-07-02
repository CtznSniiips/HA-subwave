"""Sensor entities for SUB/WAVE."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SubWaveCoordinator
from .entity import SubWaveEntity
from .util import find_last_message, get_nested as _get, truncate


@dataclass(frozen=True, kw_only=True)
class SubWaveSensorDescription(SensorEntityDescription):
    """Describes a SUB/WAVE sensor and how to pull its value/attrs from the API payload."""

    value_fn: Callable[[dict[str, Any]], Any] = lambda data: None
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _up_next_title(data: dict[str, Any]) -> str:
    upcoming = _get(data, "queueState", "upcoming", default=[]) or []
    if not upcoming:
        return "Nothing queued"
    return upcoming[0].get("title") or "Nothing queued"


def _up_next_attrs(data: dict[str, Any]) -> dict[str, Any]:
    upcoming = _get(data, "queueState", "upcoming", default=[]) or []
    next_track = upcoming[0] if upcoming else {}
    return {
        "artist": next_track.get("artist"),
        "requested_by": next_track.get("requestedBy"),
        "source": next_track.get("source"),
        "queue_length": len(upcoming),
        "queue": upcoming,
    }


def _last_request(data: dict[str, Any]) -> Any:
    """Most recent track (current or history) that was actually requested by a listener."""
    current = _get(data, "queueState", "current", default={}) or {}
    if current.get("requestedBy"):
        return current
    for track in _get(data, "queueState", "history", default=[]) or []:
        if track.get("requestedBy"):
            return track
    return None


def _last_request_name(data: dict[str, Any]) -> str:
    request = _last_request(data)
    return request["requestedBy"] if request else "None"


def _last_request_attrs(data: dict[str, Any]) -> dict[str, Any]:
    request = _last_request(data) or {}
    return {
        "title": request.get("title"),
        "artist": request.get("artist"),
        "started_at": request.get("startedAt"),
        "queued_at": request.get("queuedAt"),
    }


def _latest_dj_log(data: dict[str, Any]) -> Any:
    log = _get(data, "queueState", "djLog", default=[]) or []
    return log[0] if log else None


def _dj_activity_message(data: dict[str, Any]) -> str | None:
    entry = _latest_dj_log(data)
    return entry.get("message") if entry else None


def _dj_activity_attrs(data: dict[str, Any]) -> dict[str, Any]:
    entry = _latest_dj_log(data) or {}
    return {
        "kind": entry.get("kind"),
        "timestamp": entry.get("t"),
        "recent_log": (_get(data, "queueState", "djLog", default=[]) or [])[:10],
    }


# HA truncates entity states longer than this in the recorder/frontend, so
# long free-text sensors keep the full text in an attribute and cap the
# state itself.
_MAX_STATE_LENGTH = 255


def _dj_commentary_value(data: dict[str, Any]) -> str | None:
    link = find_last_message(data, "segment", "link")
    return truncate(link.get("text")) if link else None


def _dj_commentary_attrs(data: dict[str, Any]) -> dict[str, Any]:
    link = find_last_message(data, "segment", "link") or {}
    pick = find_last_message(data, "dj", "pick") or {}
    pick_meta = pick.get("meta") or {}
    return {
        "full_text": link.get("text"),
        "timestamp": link.get("t"),
        "pick_reasoning": pick.get("text"),
        "pick_track": pick_meta.get("title"),
        "pick_artist": pick_meta.get("artist"),
    }


def _session_value(data: dict[str, Any]) -> str:
    return _get(data, "sessionLog", "session", "kind", default="unknown")


def _session_attrs(data: dict[str, Any]) -> dict[str, Any]:
    session = _get(data, "sessionLog", "session", default={}) or {}
    messages = _get(data, "sessionLog", "messages", default=[]) or []
    scenario_events = [
        m.get("text") for m in messages if m.get("role") == "event" and m.get("kind") == "scenario"
    ]
    return {
        "id": session.get("id"),
        "key": session.get("key"),
        "show": session.get("show"),
        "started_at": session.get("startedAt"),
        "recent_scenario_events": scenario_events[-5:],
    }


SENSOR_DESCRIPTIONS: tuple[SubWaveSensorDescription, ...] = (
    SubWaveSensorDescription(
        key="dj_name",
        translation_key="dj_name",
        icon="mdi:account-voice",
        value_fn=lambda d: _get(d, "dj", "name"),
        attrs_fn=lambda d: {
            "tagline": _get(d, "dj", "tagline"),
            "station": _get(d, "dj", "station"),
            "avatar": _get(d, "dj", "avatar"),
        },
    ),
    SubWaveSensorDescription(
        key="now_playing_title",
        translation_key="now_playing_title",
        icon="mdi:music-note",
        value_fn=lambda d: _get(d, "nowPlaying", "title"),
        attrs_fn=lambda d: {
            "artist": _get(d, "nowPlaying", "artist"),
            "album": _get(d, "nowPlaying", "album"),
            "genre": _get(d, "nowPlaying", "genre"),
            "moods": _get(d, "nowPlaying", "moods"),
            "energy": _get(d, "nowPlaying", "energy"),
            "bpm": _get(d, "nowPlaying", "bpm"),
            "musical_key": _get(d, "nowPlaying", "musicalKey"),
            "year": _get(d, "nowPlaying", "year"),
            "requested_by": _get(d, "queueState", "current", "requestedBy"),
            "source": _get(d, "queueState", "current", "source"),
            "started_at": _get(d, "queueState", "current", "startedAt"),
        },
    ),
    SubWaveSensorDescription(
        key="listeners",
        translation_key="listeners",
        icon="mdi:account-group",
        native_unit_of_measurement="listeners",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _get(d, "listeners", "current", default=0),
        attrs_fn=lambda d: {"peak": _get(d, "listeners", "peak")},
    ),
    SubWaveSensorDescription(
        key="weather_condition",
        translation_key="weather_condition",
        icon="mdi:weather-partly-cloudy",
        value_fn=lambda d: _get(d, "context", "weather", "condition"),
        attrs_fn=lambda d: {
            "temp": _get(d, "context", "weather", "temp"),
            "unit": _get(d, "context", "weather", "tempUnit"),
            "location": _get(d, "context", "weather", "location"),
            "mood": _get(d, "context", "weather", "mood"),
            "is_day": _get(d, "context", "weather", "isDay"),
        },
    ),
    SubWaveSensorDescription(
        key="current_show",
        translation_key="current_show",
        icon="mdi:radio",
        value_fn=lambda d: _get(d, "context", "time", "show") or "None",
        attrs_fn=lambda d: {
            "period": _get(d, "context", "time", "period"),
            "vibe": _get(d, "context", "time", "vibe"),
            "mood": _get(d, "context", "time", "mood"),
            "dominant_mood": _get(d, "context", "dominantMood"),
            "active_show": _get(d, "activeShow"),
        },
    ),
    SubWaveSensorDescription(
        key="llm_tokens",
        translation_key="llm_tokens",
        icon="mdi:counter",
        native_unit_of_measurement="tokens",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _get(d, "llmTokens", default=0),
    ),
    SubWaveSensorDescription(
        key="up_next",
        translation_key="up_next",
        icon="mdi:playlist-music",
        value_fn=_up_next_title,
        attrs_fn=_up_next_attrs,
    ),
    SubWaveSensorDescription(
        key="last_request",
        translation_key="last_request",
        icon="mdi:account-heart",
        value_fn=_last_request_name,
        attrs_fn=_last_request_attrs,
    ),
    SubWaveSensorDescription(
        key="dj_activity",
        translation_key="dj_activity",
        icon="mdi:message-text-outline",
        value_fn=_dj_activity_message,
        attrs_fn=_dj_activity_attrs,
    ),
    SubWaveSensorDescription(
        key="dj_commentary",
        translation_key="dj_commentary",
        icon="mdi:comment-quote-outline",
        value_fn=_dj_commentary_value,
        attrs_fn=_dj_commentary_attrs,
    ),
    SubWaveSensorDescription(
        key="session",
        translation_key="session",
        icon="mdi:timeline-clock-outline",
        value_fn=_session_value,
        attrs_fn=_session_attrs,
    ),
    SubWaveSensorDescription(
        key="broadcast_status",
        translation_key="broadcast_status",
        icon="mdi:radio-tower",
        value_fn=lambda d: _get(d, "health", "status", default="unknown"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SubWaveCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SubWaveSensor(coordinator, entry.entry_id, description)
        for description in SENSOR_DESCRIPTIONS
    )


class SubWaveSensor(SubWaveEntity, SensorEntity):
    """A single derived value from the SUB/WAVE now-playing payload."""

    entity_description: SubWaveSensorDescription

    def __init__(
        self,
        coordinator: SubWaveCoordinator,
        entry_id: str,
        description: SubWaveSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data or {})
