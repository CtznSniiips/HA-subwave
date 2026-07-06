"""Switch to enable/disable the SUB/WAVE HA-side stream proxy."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import SubWaveCoordinator
from .entity import SubWaveEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SubWaveCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SubWaveStreamProxySwitch(coordinator, entry.entry_id)])


class SubWaveStreamProxySwitch(SubWaveEntity, SwitchEntity, RestoreEntity):
    """Turns SubWaveStreamProxyView on/off for this SUB/WAVE server.

    The stream proxy is intentionally unauthenticated (see http.py) so
    media players/browsers can play it without attaching HA auth headers.
    That's fine for the common case, but this switch lets you shrink the
    unauthenticated attack surface by turning the proxy off entirely when
    you don't need remote (Nabu Casa/reverse proxy) playback - e.g. while
    away, or if you're not using the proxy stream at all.

    Defaults on, since that preserves existing behavior for anyone who
    upgrades and was already relying on the proxy.
    """

    _attr_translation_key = "stream_proxy_enabled"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:lan-connect"

    def __init__(self, coordinator: SubWaveCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_stream_proxy_enabled"
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        self.coordinator.stream_proxy_enabled = self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.coordinator.stream_proxy_enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.coordinator.stream_proxy_enabled = False
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        # This is a local HA-side setting, not derived from polled SUB/WAVE
        # data, so it should stay controllable even if the coordinator's
        # last poll of SUB/WAVE failed.
        return True
