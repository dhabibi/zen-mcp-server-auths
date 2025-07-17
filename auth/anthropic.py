import base64
import hashlib
import os
import time
from typing import Optional

import requests

from . import get, set

CLIENT_ID = os.getenv("ANTHROPIC_CLIENT_ID", "")
AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
REDIRECT_URI = "https://console.anthropic.com/oauth/code/callback"
SCOPE = "org:create_api_key user:profile user:inference"


def _generate_pkce() -> dict[str, str]:
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return {"verifier": verifier, "challenge": challenge}


def generate_oauth_url() -> dict[str, str]:
    pkce = _generate_pkce()
    params = {
        "code": "true",
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "code_challenge": pkce["challenge"],
        "code_challenge_method": "S256",
        "state": pkce["verifier"],
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{AUTHORIZE_URL}?{query}"
    return {"url": url, "verifier": pkce["verifier"]}


def exchange_code(code: str, state: str, verifier: str) -> Optional[str]:
    response = requests.post(
        TOKEN_URL,
        json={
            "code": code,
            "state": state,
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier,
        },
        headers={"Content-Type": "application/json"},
    )
    if not response.ok:
        return None
    data = response.json()
    set(
        "anthropic",
        {
            "type": "oauth",
            "refresh": data.get("refresh_token"),
            "access": data.get("access_token"),
            "expires": int(time.time() * 1000 + data.get("expires_in", 0) * 1000),
        },
    )
    return data.get("access_token")


def _refresh() -> Optional[str]:
    info = get("anthropic")
    if not info or info.get("type") != "oauth":
        return None
    response = requests.post(
        TOKEN_URL,
        json={
            "grant_type": "refresh_token",
            "refresh_token": info.get("refresh"),
            "client_id": CLIENT_ID,
        },
        headers={"Content-Type": "application/json"},
    )
    if not response.ok:
        return None
    data = response.json()
    set(
        "anthropic",
        {
            "type": "oauth",
            "refresh": data.get("refresh_token"),
            "access": data.get("access_token"),
            "expires": int(time.time() * 1000 + data.get("expires_in", 0) * 1000),
        },
    )
    return data.get("access_token")


def get_access_token() -> Optional[str]:
    info = get("anthropic")
    if not info or info.get("type") != "oauth":
        return None
    access = info.get("access")
    expires = info.get("expires", 0)
    if access and expires > int(time.time() * 1000):
        return access
    return _refresh()
