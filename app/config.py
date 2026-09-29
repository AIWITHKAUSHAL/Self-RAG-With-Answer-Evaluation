import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def settings() -> dict:
    """Load server-side EURI settings, preserving existing environment values.

    Returns the API key, base URL, and model name. The result contains a secret
    and must not be returned directly by an HTTP route or written to a trace.
    """
    # Reload on each live run so adding a local key needs no server restart.
    load_dotenv(ROOT / ".env", override=False)
    return {
        "api_key": os.getenv("EURI_API_KEY", "").strip(),
        "base_url": os.getenv("EURI_BASE_URL", "https://api.euron.one/api/v1/euri"),
        "model": os.getenv("EURI_MODEL", "gemini-3.5-flash-lite"),
    }
