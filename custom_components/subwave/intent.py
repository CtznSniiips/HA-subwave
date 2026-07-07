"""Assist (voice) intent for submitting SUB/WAVE listener requests.

This only registers the intent *handler* with Home Assistant's intent
framework - it does not teach Assist how to phrase a sentence. To actually
trigger this by voice, add a custom sentence that maps to the
"SubwaveSubmitRequest" intent. See custom_sentences/en/subwave.yaml in this
repo for a ready-to-copy example (custom sentences must live under your HA
config directory at config/custom_sentences/<language>/, HACS can't install
files there automatically).
"""
from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent

from .const import ATTR_NAME, ATTR_TEXT, DOMAIN, INTENT_SUBMIT_REQUEST
from .coordinator import SubWaveRequestError


class SubWaveSubmitRequestIntent(intent.IntentHandler):
    """Handle the SubwaveSubmitRequest intent.

    Assist has no built-in concept of "which SUB/WAVE server" to target, so
    if more than one config entry is set up, this uses whichever coordinator
    was registered first. Most setups only ever run one SUB/WAVE server, so
    this keeps the common voice-control case simple; multi-server setups
    should use the subwave.submit_request service directly (e.g. from a
    scripted sentence trigger) to target a specific entry.
    """

    intent_type = INTENT_SUBMIT_REQUEST
    slot_schema = {
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_NAME): cv.string,
    }

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        slots = self.async_validate_slots(intent_obj.slots)
        text = slots[ATTR_TEXT]["value"]
        name = slots.get(ATTR_NAME, {}).get("value")

        response = intent_obj.create_response()
        coordinators = self.hass.data.get(DOMAIN, {})

        if not coordinators:
            response.async_set_speech("SUB/WAVE isn't set up.")
            return response

        coordinator = next(iter(coordinators.values()))

        try:
            await coordinator.async_submit_request(text, name)
        except SubWaveRequestError:
            response.async_set_speech(
                "I couldn't reach SUB/WAVE to submit that request."
            )
            return response

        response.async_set_speech(f"Requested {text}.")
        return response
