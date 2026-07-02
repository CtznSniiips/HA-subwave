"""Base entity for SUB/WAVE."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SubWaveCoordinator


class SubWaveEntity(CoordinatorEntity[SubWaveCoordinator]):
    """Base entity tied to a SUB/WAVE station config entry."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SubWaveCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        dj = data.get("dj") or {}
        station_name = dj.get("station") or "SUB/WAVE"
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=station_name,
            manufacturer=MANUFACTURER,
            model="AI Radio Station",
            configuration_url=self.coordinator.base_url,
        )
