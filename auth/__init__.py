import json
import os
from pathlib import Path
from typing import Any, Optional

APP_NAME = "zen-mcp-server"
DATA_DIR = Path.home() / ".local" / "share" / APP_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)
AUTH_FILE = DATA_DIR / "auth.json"


def _load_all() -> dict[str, Any]:
    if not AUTH_FILE.exists():
        return {}
    try:
        return json.loads(AUTH_FILE.read_text())
    except Exception:
        return {}


def all() -> dict[str, Any]:
    return _load_all()


def get(key: str) -> Optional[dict[str, Any]]:
    return _load_all().get(key)


def set(key: str, info: dict[str, Any]) -> None:
    data = _load_all()
    data[key] = info
    AUTH_FILE.write_text(json.dumps(data, indent=2))
    os.chmod(AUTH_FILE, 0o600)
