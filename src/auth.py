"""
Gmail MCP Server — auth.py
Handles Google OAuth2 authentication for the Gmail API.
"""

import os
import sys
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

logger = logging.getLogger(__name__)

# Gmail API scopes — readonly + modify (for mark-as-read)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "./credentials/credentials.json")
TOKEN_PATH = os.getenv("TOKEN_PATH", "./credentials/token.json")


def get_credentials() -> Credentials:
    """
    Load and return valid Google OAuth2 credentials.

    - If token.json exists and is valid: loads it directly.
    - If expired but refresh_token present: auto-refreshes.
    - If no token: opens browser for OAuth consent (first-time only).
    """
    credentials_path = Path(CREDENTIALS_PATH)
    token_path = Path(TOKEN_PATH)

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"\n❌ Credentials file not found at: {credentials_path.resolve()}\n\n"
            "Please download credentials.json from Google Cloud Console:\n"
            "  1. Go to https://console.cloud.google.com\n"
            "  2. APIs & Services → Credentials → Create OAuth2 (Desktop app)\n"
            "  3. Download and save as credentials/credentials.json\n\n"
            "See README.md for detailed instructions."
        )

    creds = None

    # Load existing token if available
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            logger.warning(f"Could not load token.json: {e}. Will re-authorize.")
            creds = None

    # Refresh or start new OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Token expired — refreshing...")
            creds.refresh(Request())
        else:
            print("\n─────────────────────────────────────────────────────")
            print("  Gmail MCP — First-Time Authorization Required")
            print("─────────────────────────────────────────────────────")
            print("\nOpening your browser for Google OAuth consent...")
            print("If it doesn't open automatically, check the terminal for a URL.\n")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            # run_local_server opens the browser and handles the redirect automatically
            creds = flow.run_local_server(port=0)

            print("\n✅ Authorization successful!\n")

        # Save the token for future runs
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
        print(f"🔑 Token saved to: {token_path.resolve()}")

    return creds


# ──────────────────────────────────────────────────────────────────────────────
# Standalone auth script — run with: python -m src.auth
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        creds = get_credentials()
        print("\n✅ Gmail authentication successful!")
        print("You can now run the MCP server: python -m src.server")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Auth failed: {e}")
        sys.exit(1)
