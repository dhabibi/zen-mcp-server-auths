"""Anthropic OAuth authentication helpers."""

import time
from typing import Optional

import requests

from utils.pkce import generate_pkce

from . import utils

CLIENT_ID = "c4aa5311-7756-40f1-aa81-b2c43ff8869e"
AUTH_URL = "https://claude.ai/oauth/authorize"
TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
REDIRECT_URI = "https://console.anthropic.com/oauth/code/callback"
SCOPE = "org:create_api_key user:profile user:inference"


def start_oauth() -> tuple[str, str]:
    """Return authorize URL and verifier."""
    pkce = generate_pkce()
    url = (
        requests.Request(
            "GET",
            AUTH_URL,
            params={
                "code": "true",
                "client_id": CLIENT_ID,
                "response_type": "code",
                "redirect_uri": REDIRECT_URI,
                "scope": SCOPE,
                "code_challenge": pkce.challenge,
                "code_challenge_method": "S256",
                "state": pkce.verifier,
            },
        )
        .prepare()
        .url
    )
    return url, pkce.verifier


def exchange_code(code: str, state: str, verifier: str) -> Optional[str]:
    """Exchange authorization code for access token."""
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
    utils.set(
        "anthropic",
        {
            "type": "oauth",
            "refresh": data["refresh_token"],
            "access": data["access_token"],
            "expires": int(time.time() * 1000) + data["expires_in"] * 1000,
        },
    )
    return data.get("access_token")


def get_token() -> Optional[str]:
    """Return a valid access token, refreshing if needed."""
    info = utils.get("anthropic")
    if not info or info.get("type") != "oauth":
        return None
    access = info.get("access")
    if access and info.get("expires", 0) > int(time.time() * 1000):
        return access
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
    utils.set(
        "anthropic",
        {
            "type": "oauth",
            "refresh": data["refresh_token"],
            "access": data["access_token"],
            "expires": int(time.time() * 1000) + data["expires_in"] * 1000,
        },
    )
    return data.get("access_token")
