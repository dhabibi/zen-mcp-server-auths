import base64
import hashlib
import os
from dataclasses import dataclass


@dataclass
class PKCE:
    verifier: str
    challenge: str


def generate_pkce() -> PKCE:
    """Generate PKCE verifier and challenge."""
    verifier_bytes = os.urandom(32)
    verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=").decode()
    challenge_digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(challenge_digest).rstrip(b"=").decode()
    return PKCE(verifier=verifier, challenge=challenge)
