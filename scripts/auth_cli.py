"""Simple CLI for managing authentication credentials."""

from __future__ import annotations

from auth.anthropic import exchange_code, oauth_url
from auth.github_copilot import get_copilot_token, poll_oauth_token, start_device_flow


def select_provider() -> str:
    print("\nAdd credential\n")
    print("Select provider")
    print("1) Anthropic (recommended)")
    print("2) GitHub Copilot")
    choice = input("Enter number: ").strip()
    if choice == "1":
        return "anthropic"
    if choice == "2":
        return "github-copilot"
    raise SystemExit("Unknown choice")


def anthropic_flow() -> None:
    url, verifier = oauth_url()
    print("\nOpen the following URL in your browser and complete login:\n")
    print(url)
    print("\nAfter granting access, you will be redirected to a URL containing 'code' and 'state' parameters.")
    code = input("Enter the value of 'code': ").strip()
    state = input("Enter the value of 'state': ").strip()
    token = exchange_code(code, state, verifier)
    if token:
        print("Anthropic credentials saved.")
    else:
        print("Authentication failed.")


def copilot_flow() -> None:
    data = start_device_flow()
    print("\nVisit", data["verification_uri"], "and enter code", data["user_code"])
    print("Waiting for authorization...")
    token = poll_oauth_token(data["device_code"], data.get("interval", 5))
    if not token:
        print("Authorization failed.")
        return
    api_token = get_copilot_token()
    if api_token:
        print("GitHub Copilot credentials saved.")
    else:
        print("Failed to obtain Copilot API token.")


def main() -> None:
    provider = select_provider()
    if provider == "anthropic":
        anthropic_flow()
    elif provider == "github-copilot":
        copilot_flow()


if __name__ == "__main__":
    main()
