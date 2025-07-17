"""GitHub Copilot authentication helpers.

Implements the device code OAuth flow and token retrieval
for the Copilot API used by OpenCode.
"""

from __future__ import annotations

import os
import time

import httpx

from . import Info, get, set

CLIENT_ID = os.getenv("GITHUB_COPILOT_CLIENT_ID", "d8e2041f4ccf400ab4d8")
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
COPILOT_API_KEY_URL = "https://api.github.com/copilot_internal/v2/token"
USER_AGENT = "GitHubCopilotChat/0.26.7"


def start_device_flow() -> dict:
    """Initiate the device authorization flow."""

    resp = httpx.post(
        DEVICE_CODE_URL,
        json={"client_id": CLIENT_ID, "scope": "read:user"},
        headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": USER_AGENT},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def poll_oauth_token(device_code: str, interval: int) -> str | None:
    """Poll GitHub until an OAuth token is returned."""

    while True:
        time.sleep(interval)
        resp = httpx.post(
            ACCESS_TOKEN_URL,
            json={
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": USER_AGENT},
            timeout=30.0,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("access_token"):
            info = Info(type="oauth", refresh=data["access_token"], access="", expires=0)
            set("github-copilot", info)
            return data["access_token"]
        if data.get("error") not in ("authorization_pending", "slow_down"):
            return None


def get_copilot_token() -> str | None:
    """Return a valid Copilot API token, retrieving one if necessary."""

    info = get("github-copilot")
    if not info or info.type != "oauth":
        return None
    if info.access and info.expires > int(time.time() * 1000):
        return info.access

    resp = httpx.get(
        COPILOT_API_KEY_URL,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {info.refresh}",
            "User-Agent": USER_AGENT,
            "Editor-Version": "vscode/1.99.3",
            "Editor-Plugin-Version": "copilot-chat/0.26.7",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    new_info = Info(
        type="oauth",
        refresh=info.refresh,
        access=data["token"],
        expires=int(data["expires_at"]) * 1000,
    )
    set("github-copilot", new_info)
    return new_info.access
