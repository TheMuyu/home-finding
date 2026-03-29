import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

TRAFIKLAB_RESROBOT_KEY = os.getenv("TRAFIKLAB_RESROBOT_KEY", "")
TRAFIKLAB_STOPS_KEY = os.getenv("TRAFIKLAB_STOPS_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FLASK_SECRET_KEY = os.getenv(
    "FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

_API_KEY_REGISTRY = [
    {
        "key": "TRAFIKLAB_RESROBOT_KEY",
        "value": TRAFIKLAB_RESROBOT_KEY,
        "feature": "Transit journey planning (commute times)",
    },
    {
        "key": "TRAFIKLAB_STOPS_KEY",
        "value": TRAFIKLAB_STOPS_KEY,
        "feature": "Nearby transit stops lookup",
    },
    {
        "key": "ANTHROPIC_API_KEY",
        "value": ANTHROPIC_API_KEY,
        "feature": "AI scoring and district recommendations",
    },
    {
        "key": "GOOGLE_MAPS_API_KEY",
        "value": GOOGLE_MAPS_API_KEY,
        "feature": "Enhanced geocoding accuracy (optional — free Nominatim used if absent)",
        "optional": True,
    },
]


def get_missing_api_keys():
    """Return list of missing (non-optional required) API keys with feature descriptions."""
    missing = []
    for entry in _API_KEY_REGISTRY:
        if not entry["value"] and not entry.get("optional"):
            missing.append({"key": entry["key"], "feature": entry["feature"]})
    return missing


def get_all_key_statuses():
    """Return status of all API keys (for informational display)."""
    statuses = []
    for entry in _API_KEY_REGISTRY:
        statuses.append(
            {
                "key": entry["key"],
                "feature": entry["feature"],
                "set": bool(entry["value"]),
                "optional": entry.get("optional", False),
            }
        )
    return statuses
