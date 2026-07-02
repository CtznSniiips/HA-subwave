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


def _get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely walk a chain of nested dict keys."""
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


@dataclass(frozen=True, kw_only=True)
class SubWaveSensorDescription(SensorEntityDescription):
    """Describes a SUB/WAVE sensor and how to pull its value/attrs from the API payload."""

    value_fn: Callable[[dict[str, Any]], Any] = lambda data: None
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


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
