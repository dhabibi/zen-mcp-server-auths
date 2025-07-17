import os
import time
from typing import Optional

import requests

from . import get, set

CLIENT_ID = os.getenv("GITHUB_COPILOT_CLIENT_ID", "d1b5d6e646903b9ee0ac")
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
COPILOT_API_KEY_URL = "https://api.github.com/copilot_internal/v2/token"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "GitHubCopilotChat/0.26.7",
}


def start_device_flow() -> dict[str, any]:
    resp = requests.post(
        DEVICE_CODE_URL,
        headers=HEADERS,
        json={"client_id": CLIENT_ID, "scope": "read:user"},
    )
    data = resp.json()
    return {
        "device": data.get("device_code"),
        "user": data.get("user_code"),
        "verification": data.get("verification_uri"),
        "interval": data.get("interval", 5),
        "expiry": data.get("expires_in"),
    }


def poll_token(device_code: str) -> str:
    resp = requests.post(
        ACCESS_TOKEN_URL,
        headers=HEADERS,
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
        set(
            "github-copilot",
            {
                "type": "oauth",
                "refresh": data["access_token"],
                "access": "",
                "expires": 0,
            },
        )
        return "complete"
    return data.get("error", "pending")


def get_api_token() -> Optional[str]:
    info = get("github-copilot")
    if not info or info.get("type") != "oauth":
        return None
    if info.get("access") and info.get("expires", 0) > int(time.time() * 1000):
        return info["access"]
    resp = requests.get(
        COPILOT_API_KEY_URL,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {info['refresh']}",
            "User-Agent": "GitHubCopilotChat/0.26.7",
            "Editor-Version": "vscode/1.99.3",
            "Editor-Plugin-Version": "copilot-chat/0.26.7",
        },
    )
    data = resp.json()
    token = data.get("token")
    if token:
        set(
            "github-copilot",
            {
                "type": "oauth",
                "refresh": info["refresh"],
                "access": token,
                "expires": data.get("expires_at", 0) * 1000,
            },
        )
    return token
