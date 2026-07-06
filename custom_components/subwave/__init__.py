"""The SUB/WAVE integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import SubWaveCoordinator
from .frontend import async_register_frontend
from .http import SubWaveRequestProxyView, SubWaveStreamProxyView

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]

_HUB_REGISTERED_KEY = f"{DOMAIN}_hub_registered"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SUB/WAVE from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = SubWaveCoordinator(hass, host, port, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # The HTTP views and frontend card are registered once for the whole HA
    # instance (not per config entry) - the proxy views are keyed by
    # entry_id in their URL, and the Lovelace card can point at any
    # SUB/WAVE media_player entity, so all SUB/WAVE servers share these.
    if not hass.data.get(_HUB_REGISTERED_KEY):
        hass.http.register_view(SubWaveStreamProxyView(hass))
        hass.http.register_view(SubWaveRequestProxyView(hass))
        await async_register_frontend(hass)
        hass.data[_HUB_REGISTERED_KEY] = True

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change (e.g. polling interval)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
