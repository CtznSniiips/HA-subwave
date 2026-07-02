"""Serves the bundled SUB/WAVE Lovelace card and registers it as a frontend module.

Because this is injected via add_extra_js_url(), users don't need to
manually add a Lovelace resource in Settings -> Dashboards -> Resources -
the card is just available as `custom:subwave-card` once the integration
is set up.
"""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.core import HomeAssistant

from .const import CARD_FILENAME, CARD_URL_BASE

WWW_DIR = Path(__file__).parent / "www"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve custom_components/subwave/www/ and inject the card as a module.

    Call once per HA instance - the caller in __init__.py guards against
    calling this more than once even with multiple SUB/WAVE config entries,
    since registering the same static path twice raises.
    """
    await _async_register_static_path(hass, CARD_URL_BASE, str(WWW_DIR))
    add_extra_js_url(hass, f"{CARD_URL_BASE}/{CARD_FILENAME}")


async def _async_register_static_path(hass: HomeAssistant, url_path: str, dir_path: str) -> None:
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(url_path, dir_path, cache_headers=False)]
        )
    except ImportError:
        # Home Assistant < 2024.7 doesn't have the async static path API -
        # fall back to the deprecated synchronous one.
        hass.http.register_static_path(url_path, dir_path, cache_headers=False)
