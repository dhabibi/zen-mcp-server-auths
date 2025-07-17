import argparse
import time

from auth import anthropic as auth_anthropic
from auth import github_copilot as auth_copilot


def prompt_provider() -> str:
    print("Select provider:")
    print("1) Anthropic (recommended)")
    print("2) GitHub Copilot")
    choice = input("Enter number: ").strip()
    return "anthropic" if choice == "1" else "github-copilot"


def anthropic_flow():
    result = auth_anthropic.generate_oauth_url()
    print("Open the following URL in your browser and authorize:")
    print(result["url"])
    code = input("Enter the returned code: ").strip()
    state = input("Enter the returned state: ").strip()
    token = auth_anthropic.exchange_code(code, state, result["verifier"])
    if token:
        print("Anthropic authentication complete")
    else:
        print("Authentication failed")


def copilot_flow():
    step = auth_copilot.start_device_flow()
    print(f"Visit {step['verification']} and enter code {step['user']}")
    device = step["device"]
    interval = step["interval"]
    expiry = step["expiry"]
    start = time.time()
    while time.time() - start < expiry:
        status = auth_copilot.poll_token(device)
        if status == "complete":
            break
        elif status == "failed":
            print("Authentication failed")
            return
        time.sleep(interval)
    if status != "complete":
        print("Timed out")
        return
    token = auth_copilot.get_api_token()
    if token:
        print("GitHub Copilot authentication complete")
    else:
        print("Failed to retrieve API token")


def main():
    parser = argparse.ArgumentParser(description="Authenticate providers")
    parser.add_argument("login", nargs="?", help="login command")
    parser.add_argument("provider", nargs="?", help="provider name")
    args = parser.parse_args()

    if args.login != "login":
        parser.print_help()
        return

    provider = args.provider or prompt_provider()
    if provider == "anthropic":
        anthropic_flow()
    elif provider == "github-copilot":
        copilot_flow()
    else:
        print("Unknown provider")


if __name__ == "__main__":
    main()
