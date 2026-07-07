"""HTTP view that proxies the SUB/WAVE stream through Home Assistant.

Registering this on HA's own webserver means the stream becomes reachable
anywhere HA itself is reachable (Nabu Casa remote access, a reverse proxy
in front of HA, etc.) without exposing the SUB/WAVE server directly to the
internet.
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import DOMAIN, STREAM_FORMATS
from .coordinator import SubWaveRequestError

_LOGGER = logging.getLogger(__name__)

CHUNK_SIZE = 8192


class SubWaveStreamProxyView(HomeAssistantView):
    """Proxies /stream.<fmt> from a SUB/WAVE server through Home Assistant.

    Registered once for the whole HA instance at:
        /api/subwave/{entry_id}/stream.{fmt}

    Multiple SUB/WAVE servers (config entries) share this single view;
    entry_id in the URL picks which one to proxy.
    """

    url = "/api/subwave/{entry_id}/stream.{fmt}"
    name = "api:subwave:stream"
    # Media players/cast targets/browsers streaming audio can't attach HA's
    # auth headers, so this endpoint is intentionally unauthenticated - same
    # approach HA core uses for its camera stream proxies. It only ever
    # forwards read-only audio bytes from a URL already known to HA.
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(
        self, request: web.Request, entry_id: str, fmt: str
    ) -> web.StreamResponse:
        if fmt not in STREAM_FORMATS:
            return web.Response(status=404, text="Unknown stream format")

        coordinators = self.hass.data.get(DOMAIN, {})
        coordinator = coordinators.get(entry_id)
        if coordinator is None:
            return web.Response(status=404, text="Unknown SUB/WAVE server")

        if not getattr(coordinator, "stream_proxy_enabled", True):
            return web.Response(status=403, text="Stream proxy is disabled")

        upstream_url = coordinator.stream_url(fmt)
        session = async_get_clientsession(self.hass)

        try:
            upstream = await session.get(
                upstream_url, timeout=aiohttp.ClientTimeout(total=None)
            )
        except aiohttp.ClientError as err:
            _LOGGER.warning(
                "Could not reach SUB/WAVE stream at %s: %s", upstream_url, err
            )
            return web.Response(status=502, text="Upstream stream unavailable")

        response = web.StreamResponse(
            status=upstream.status,
            headers={
                "Content-Type": upstream.headers.get("Content-Type", "audio/mpeg"),
                "Cache-Control": "no-cache",
            },
        )
        await response.prepare(request)

        try:
            async for chunk in upstream.content.iter_chunked(CHUNK_SIZE):
                await response.write(chunk)
        except (aiohttp.ClientError, ConnectionResetError):
            # Client disconnected or upstream dropped - nothing to do.
            pass
        finally:
            upstream.close()

        return response


class SubWaveRequestProxyView(HomeAssistantView):
    """Proxies POST /api/requests to SUB/WAVE for the Lovelace card.

    Registered once for the whole HA instance at:
        /api/subwave/{entry_id}/requests

    Unlike the stream/image proxies, this performs a real write against
    SUB/WAVE, so it keeps HA's normal authentication requirement (the
    HomeAssistantView default). The Lovelace card calls this via
    hass.callApi(), which already attaches the logged-in user's auth token -
    so this also "just works" through Nabu Casa/a reverse proxy the same
    way the rest of the frontend does, with no extra setup.
    """

    url = "/api/subwave/{entry_id}/requests"
    name = "api:subwave:requests"

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request, entry_id: str) -> web.Response:
        coordinators = self.hass.data.get(DOMAIN, {})
        coordinator = coordinators.get(entry_id)
        if coordinator is None:
            return web.json_response({"error": "Unknown SUB/WAVE server"}, status=404)

        try:
            payload = await request.json()
        except (ValueError, aiohttp.ContentTypeError):
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        text = (payload or {}).get("text")
        if not text or not isinstance(text, str):
            return web.json_response({"error": '"text" is required'}, status=400)

        name = (payload or {}).get("name")
        if not isinstance(name, str):
            name = None

        try:
            parsed = await coordinator.async_submit_request(text, name)
        except SubWaveRequestError as err:
            _LOGGER.warning("Failed to submit SUB/WAVE request: %s", err)
            return web.json_response({"error": "Could not reach SUB/WAVE"}, status=502)

        status = parsed.pop("_status")
        return web.json_response(parsed, status=status)


def get_proxy_stream_url(
    hass: HomeAssistant,
    entry_id: str,
    fmt: str = "mp3",
    *,
    prefer_external: bool | None = None,
) -> str | None:
    """Build the HA-proxied stream URL, or None if no usable base URL exists.

    Tries Nabu Casa / configured external URL / internal URL / IP, in that
    order (via allow_cloud/allow_external/allow_internal/allow_ip). Set
    prefer_external=True to bias toward the externally-reachable URL even
    when called from a context where HA thinks it's "local".

    Returns None if the stream proxy switch has been turned off for this
    entry_id, in addition to the existing "no usable base URL" case.
    """
    coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
    if coordinator is not None and not getattr(coordinator, "stream_proxy_enabled", True):
        return None

    try:
        base = get_url(
            hass,
            allow_internal=True,
            allow_external=True,
            allow_cloud=True,
            allow_ip=True,
            prefer_external=prefer_external,
        )
    except NoURLAvailableError:
        return None
    return f"{base}/api/subwave/{entry_id}/stream.{fmt}"
