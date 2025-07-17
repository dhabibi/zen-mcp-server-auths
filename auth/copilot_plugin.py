"""Optional dynamic loader for GitHub Copilot auth logic.

This mirrors the lazy loading mechanism from OpenCode. The helper downloads
an auth script from GitHub and imports it at runtime if available.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType

import httpx

STATE_DIR = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "zen-mcp-server"
PLUGIN_PATH = STATE_DIR / "plugin" / "copilot.py"


def load_remote() -> ModuleType | None:
    """Download and import the remote Copilot auth module."""

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PLUGIN_PATH.parent.mkdir(parents=True, exist_ok=True)
    url = "https://raw.githubusercontent.com/sst/opencode-github-copilot/refs/heads/main/auth.py"
    try:
        resp = httpx.get(url, timeout=10.0)
        if resp.status_code == 200:
            PLUGIN_PATH.write_text(resp.text)
    except Exception:
        return None

    if not PLUGIN_PATH.exists():
        return None

    spec = importlib.util.spec_from_file_location("copilot_plugin", str(PLUGIN_PATH))
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[arg-type]
    except Exception:
        return None
    return module
