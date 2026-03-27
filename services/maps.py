"""
Geocoding service.

Default: OpenStreetMap Nominatim (free, no key needed, 1 req/sec).
If GOOGLE_MAPS_API_KEY is set: uses Google Geocoding API (better accuracy).

Cache: simple in-process dict — avoids re-geocoding same address.
"""
import logging
import time

import requests

from config import GOOGLE_MAPS_API_KEY

logger = logging.getLogger(__name__)

_NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
_GOOGLE_BASE = "https://maps.googleapis.com/maps/api"
_USER_AGENT = "StockholmApartmentFinder/1.0 (personal project)"

# In-process cache: address string → {"lat": float, "lng": float, "formatted": str}
_geocode_cache: dict[str, dict] = {}
_last_nominatim_call: float = 0.0


def _nominatim_sleep():
    """Ensure at least 1 second between Nominatim requests (policy)."""
    global _last_nominatim_call
    elapsed = time.time() - _last_nominatim_call
    if elapsed < 1.05:
        time.sleep(1.05 - elapsed)
    _last_nominatim_call = time.time()


def geocode_address(address: str) -> dict | None:
    """
    Geocode an address string → {"lat": float, "lng": float, "formatted": str}.
    Returns None if geocoding fails or address is empty.
    """
    if not address or not address.strip():
        return None

    key = address.strip().lower()
    if key in _geocode_cache:
        return _geocode_cache[key]

    if GOOGLE_MAPS_API_KEY:
        result = _geocode_google(address)
    else:
        result = _geocode_nominatim(address)

    if result:
        _geocode_cache[key] = result
    return result


def _geocode_nominatim(address: str) -> dict | None:
    _nominatim_sleep()
    try:
        resp = requests.get(
            f"{_NOMINATIM_BASE}/search",
            params={"q": address, "format": "json", "limit": 1, "countrycodes": "se"},
            headers={"User-Agent": _USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            # Retry without country restriction (some addresses include "Stockholm" already)
            _nominatim_sleep()
            resp = requests.get(
                f"{_NOMINATIM_BASE}/search",
                params={"q": address, "format": "json", "limit": 1},
                headers={"User-Agent": _USER_AGENT},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json()
        if results:
            r = results[0]
            return {
                "lat": float(r["lat"]),
                "lng": float(r["lon"]),
                "formatted": r.get("display_name", address),
            }
    except Exception as e:
        logger.warning(f"Nominatim geocoding failed for '{address}': {e}")
    return None


def _geocode_google(address: str) -> dict | None:
    try:
        resp = requests.get(
            f"{_GOOGLE_BASE}/geocode/json",
            params={"address": address, "key": GOOGLE_MAPS_API_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return {
                "lat": loc["lat"],
                "lng": loc["lng"],
                "formatted": data["results"][0].get("formatted_address", address),
            }
        logger.warning(f"Google geocoding returned status '{data.get('status')}' for '{address}'")
    except Exception as e:
        logger.warning(f"Google geocoding failed for '{address}': {e}")
    return None
