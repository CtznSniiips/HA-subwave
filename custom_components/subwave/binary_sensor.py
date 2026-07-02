"""Binary sensor for SUB/WAVE stream status."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SubWaveCoordinator
from .entity import SubWaveEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SubWaveCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SubWaveStreamOnline(coordinator, entry.entry_id)])


class SubWaveStreamOnline(SubWaveEntity, BinarySensorEntity):
    """Reflects the streamOnline flag from the API."""

    _attr_translation_key = "stream_online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: SubWaveCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_stream_online"

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("streamOnline"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        stream = data.get("stream") or {}
        return {
            "bitrate": data.get("streamBitrate"),
            "mount": stream.get("mount"),
            "format": stream.get("format"),
            "sample_rate": stream.get("sampleRate"),
            "channels": stream.get("channels"),
            "opus_enabled": stream.get("opusEnabled"),
            "flac_enabled": stream.get("flacEnabled"),
            "aac_enabled": stream.get("aacEnabled"),
        }
