"""Config flow for SUB/WAVE."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_NOW_PLAYING,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


async def _validate_connection(hass: HomeAssistant, host: str, port: int) -> dict[str, Any]:
    """Try to reach the now-playing endpoint and return the parsed payload."""
    session = async_get_clientsession(hass)
    url = f"http://{host}:{port}{API_NOW_PLAYING}"
    async with asyncio.timeout(10):
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()


class SubWaveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SUB/WAVE."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            self._async_abort_entries_match({CONF_HOST: host, CONF_PORT: port})

            try:
                data = await _validate_connection(self.hass, host, port)
            except (aiohttp.ClientError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                dj = (data or {}).get("dj") or {}
                station = dj.get("station") or DEFAULT_NAME
                return self.async_create_entry(
                    title=station,
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SubWaveOptionsFlow:
        return SubWaveOptionsFlow(config_entry)


class SubWaveOptionsFlow(config_entries.OptionsFlow):
    """Handle options for SUB/WAVE (polling interval)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
