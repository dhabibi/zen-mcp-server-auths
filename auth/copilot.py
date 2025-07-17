"""GitHub Copilot authentication via device flow."""

import time
from typing import Optional

import requests

from . import utils

CLIENT_ID = "d6b8c347b1a98ba3f2cd"
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
COPILOT_TOKEN_URL = "https://api.githubcopilot.com/tokens"


def start_device_flow() -> dict[str, str]:
    """Begin the device authorization flow."""
    resp = requests.post(
        DEVICE_CODE_URL,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Zen-MCP-Auth",
        },
        json={"client_id": CLIENT_ID, "scope": "read:user"},
    )
    data = resp.json()
    return {
        "device": data["device_code"],
        "user": data["user_code"],
        "verification": data["verification_uri"],
        "interval": data.get("interval", 5),
        "expiry": data["expires_in"],
    }


def poll_device_token(device_code: str) -> str:
    """Poll GitHub for OAuth token."""
    resp = requests.post(
        ACCESS_TOKEN_URL,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Zen-MCP-Auth",
        },
        json={
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        },
    )
    if not resp.ok:
        return "failed"
    data = resp.json()
    if "access_token" in data:
        utils.set(
            "github-copilot",
            {"type": "oauth", "refresh": data["access_token"], "access": "", "expires": 0},
        )
        return "complete"
    return data.get("error", "pending")


def get_copilot_token() -> Optional[str]:
    """Return a Copilot API token, refreshing if necessary."""
    info = utils.get("github-copilot")
    if not info or info.get("type") != "oauth":
        return None
    if info.get("access") and info.get("expires", 0) > int(time.time() * 1000):
        return info["access"]
    resp = requests.get(
        COPILOT_TOKEN_URL,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {info['refresh']}",
            "User-Agent": "Zen-MCP-Auth",
            "Editor-Version": "vscode/1.99.3",
            "Editor-Plugin-Version": "copilot-chat/0.26.7",
        },
    )
    if not resp.ok:
        return None
    data = resp.json()
    utils.set(
        "github-copilot",
        {
            "type": "oauth",
            "refresh": info["refresh"],
            "access": data["token"],
            "expires": data["expires_at"] * 1000,
        },
    )
    return data["token"]
