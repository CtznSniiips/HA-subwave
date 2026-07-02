"""Small shared helpers for the SUB/WAVE integration."""
from __future__ import annotations

from typing import Any


def get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely walk a chain of nested dict keys, returning default if missing."""
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


def find_last_message(data: dict[str, Any], role: str, kind: str) -> dict[str, Any] | None:
    """Find the most recent /api/session message matching role/kind.

    Session messages are chronological (oldest first), so scan from the end.
    """
    messages = get_nested(data, "sessionLog", "messages", default=[]) or []
    for msg in reversed(messages):
        if msg.get("role") == role and msg.get("kind") == kind:
            return msg
    return None


# HA truncates entity states longer than this in the recorder/frontend, so
# long free-text values keep the full text elsewhere (an attribute, or a
# dedicated sensor's attrs) and cap the state/attribute value itself.
MAX_STATE_LENGTH = 255


def truncate(text: str | None, max_length: int = MAX_STATE_LENGTH) -> str | None:
    if text is None:
        return None
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"
