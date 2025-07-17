import argparse
import time

from auth import Anthropic, Copilot


def login_anthropic() -> None:
    url, verifier = Anthropic.start_oauth()
    print("Open the following URL in your browser and authorize:")
    print(url)
    code_input = input("Paste the returned 'code|state' value: ")
    try:
        code, state = code_input.strip().split("|")
    except ValueError:
        print("Invalid code format")
        return
    token = Anthropic.exchange_code(code, state, verifier)
    if token:
        print("Anthropic credentials saved")
    else:
        print("Authorization failed")


def login_copilot() -> None:
    data = Copilot.start_device_flow()
    print("Visit", data["verification"], "and enter code", data["user"])
    print("Waiting for authorization...")
    expiry = time.time() + data["expiry"]
    while time.time() < expiry:
        status = Copilot.poll_device_token(data["device"])
        if status == "complete":
            print("GitHub authorization complete")
            break
        if status == "failed":
            print("Authorization failed")
            return
        time.sleep(data["interval"])
    else:
        print("Authorization timed out")


def login() -> None:
    choices = {"1": ("Anthropic", login_anthropic), "2": ("GitHub Copilot", login_copilot)}
    print("Select provider:")
    for key, (name, _) in choices.items():
        print(f"{key}. {name}")
    selection = input("Provider: ").strip()
    if selection in choices:
        choices[selection][1]()
    else:
        print("Invalid selection")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage authentication")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("login")
    args = parser.parse_args()

    if args.command == "login":
        login()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
