"""Credential storage utilities for Zen MCP Server.

This module replicates the simple credential storage
mechanism used by OpenCode. Credentials are persisted in a
JSON file located in ``~/.local/share/zen-mcp-server/auth.json``.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "zen-mcp-server"
AUTH_FILE = DATA_DIR / "auth.json"


@dataclass
class Info:
    """Credential information structure."""

    type: str
    refresh: str
    access: str
    expires: int


def _load() -> dict[str, Any]:
    if AUTH_FILE.exists():
        try:
            with AUTH_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def all() -> dict[str, Any]:
    """Return all stored credentials."""

    return _load()


def get(key: str) -> Info | None:
    data = _load()
    value = data.get(key)
    if value is None:
        return None
    try:
        return Info(**value)
    except Exception:
        return None


def set(key: str, info: Info) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = _load()
    data[key] = asdict(info)
    with AUTH_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.chmod(AUTH_FILE, 0o600)
