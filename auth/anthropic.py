"""Anthropic authentication helpers.

These functions implement the OAuth flow used by OpenCode for
obtaining and refreshing Anthropic API tokens.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time

import httpx

from . import Info, get, set

CLIENT_ID = os.getenv("ANTHROPIC_CLIENT_ID", "opencode")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def generate_pkce() -> tuple[str, str]:
    """Return (verifier, challenge) for PKCE OAuth."""

    verifier_bytes = secrets.token_bytes(32)
    verifier = _b64url(verifier_bytes)
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


def oauth_url() -> tuple[str, str]:
    """Return OAuth URL and verifier for login."""

    verifier, challenge = generate_pkce()
    url = httpx.URL("https://claude.ai/oauth/authorize")
    url = url.copy_add_param("code", "true")
    url = url.copy_add_param("client_id", CLIENT_ID)
    url = url.copy_add_param("response_type", "code")
    url = url.copy_add_param("redirect_uri", "https://console.anthropic.com/oauth/code/callback")
    url = url.copy_add_param("scope", "org:create_api_key user:profile user:inference")
    url = url.copy_add_param("code_challenge", challenge)
    url = url.copy_add_param("code_challenge_method", "S256")
    url = url.copy_add_param("state", verifier)
    return str(url), verifier


def exchange_code(code: str, state: str, verifier: str) -> str | None:
    """Exchange authorization code for tokens and store them."""

    response = httpx.post(
        "https://console.anthropic.com/v1/oauth/token",
        json={
            "code": code,
            "state": state,
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": "https://console.anthropic.com/oauth/code/callback",
            "code_verifier": verifier,
        },
        headers={"Content-Type": "application/json"},
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    info = Info(
        type="oauth",
        refresh=data["refresh_token"],
        access=data["access_token"],
        expires=int(time.time() * 1000) + int(data["expires_in"]) * 1000,
    )
    set("anthropic", info)
    return data["access_token"]


def get_access_token() -> str | None:
    """Return a valid Anthropic access token, refreshing if needed."""

    info = get("anthropic")
    if not info or info.type != "oauth":
        return None
    if info.access and info.expires > int(time.time() * 1000):
        return info.access
    response = httpx.post(
        "https://console.anthropic.com/v1/oauth/token",
        json={
            "grant_type": "refresh_token",
            "refresh_token": info.refresh,
            "client_id": CLIENT_ID,
        },
        headers={"Content-Type": "application/json"},
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    new_info = Info(
        type="oauth",
        refresh=data["refresh_token"],
        access=data["access_token"],
        expires=int(time.time() * 1000) + int(data["expires_in"]) * 1000,
    )
    set("anthropic", new_info)
    return new_info.access
