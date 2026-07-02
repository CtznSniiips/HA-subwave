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
