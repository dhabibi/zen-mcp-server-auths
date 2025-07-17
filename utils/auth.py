import json
import os
from pathlib import Path
from typing import Any, Optional

APP_NAME = "zen-mcp-server"


def _filepath() -> Path:
    data_dir = Path.home() / ".local" / "share" / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "auth.json"


def load_all() -> dict[str, Any]:
    """Load all stored auth info."""
    file = _filepath()
    if not file.exists():
        return {}
    try:
        with open(file, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get(key: str) -> Optional[dict[str, Any]]:
    """Get auth info for provider."""
    return load_all().get(key)


def set(key: str, info: dict[str, Any]) -> None:
    """Store auth info for provider and restrict file permissions."""
    data = load_all()
    data[key] = info
    file = _filepath()
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(file, 0o600)
    except OSError:
        pass
