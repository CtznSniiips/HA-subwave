"""The SUB/WAVE integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, intent as intent_helper, selector

from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_NAME,
    ATTR_TEXT,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_SUBMIT_REQUEST,
)
from .coordinator import SubWaveCoordinator, SubWaveRequestError
from .frontend import async_register_frontend
from .http import SubWaveRequestProxyView, SubWaveStreamProxyView
from .intent import SubWaveSubmitRequestIntent

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]

_HUB_REGISTERED_KEY = f"{DOMAIN}_hub_registered"

SERVICE_SUBMIT_REQUEST_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): selector.ConfigEntrySelector(
            {"integration": DOMAIN}
        ),
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_NAME): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SUB/WAVE from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = SubWaveCoordinator(hass, host, port, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # The HTTP views, frontend card, service, and intent are registered once
    # for the whole HA instance (not per config entry) - the proxy views are
    # keyed by entry_id in their URL, the Lovelace card can point at any
    # SUB/WAVE media_player entity, and the service/intent take the target
    # entry as a parameter, so all SUB/WAVE servers share these.
    if not hass.data.get(_HUB_REGISTERED_KEY):
        hass.http.register_view(SubWaveStreamProxyView(hass))
        hass.http.register_view(SubWaveRequestProxyView(hass))
        await async_register_frontend(hass)

        async def _async_handle_submit_request(call: ServiceCall) -> None:
            """Handle the subwave.submit_request service call."""
            target_entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
            target_coordinator: SubWaveCoordinator | None = hass.data.get(
                DOMAIN, {}
            ).get(target_entry_id)
            if target_coordinator is None:
                raise ServiceValidationError(
                    f"Unknown SUB/WAVE server (config entry {target_entry_id})"
                )

            try:
                await target_coordinator.async_submit_request(
                    call.data[ATTR_TEXT], call.data.get(ATTR_NAME)
                )
            except SubWaveRequestError as err:
                raise HomeAssistantError(str(err)) from err

        hass.services.async_register(
            DOMAIN,
            SERVICE_SUBMIT_REQUEST,
            _async_handle_submit_request,
            schema=SERVICE_SUBMIT_REQUEST_SCHEMA,
        )
        intent_helper.async_register(hass, SubWaveSubmitRequestIntent(hass))

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
