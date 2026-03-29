"""
OpenStreetMap Overpass API service.

Free, no API key required. Be polite: 1 request/second max.
Queries nearby POIs within a radius of a listing's coordinates.
"""
import logging
import math
import time

import requests

logger = logging.getLogger(__name__)

_OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]
_last_call: float = 0.0


def _sleep():
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_call = time.time()


def get_nearby_pois(lat: float, lng: float, radius_m: int = 1000) -> dict:
    """
    Query nearby points of interest via Overpass API.

    Returns:
        {
            "supermarkets": [{"name": str, "lat": float, "lng": float, "distance_m": int}],
            "parks":        [...],
            "gyms":         [...],
        }
    """
    query = _build_query(lat, lng, radius_m)
    _sleep()

    last_exc = None
    elements = None
    for url in _OVERPASS_URLS:
        try:
            resp = requests.post(
                url,
                data={"data": query},
                headers={
                    "User-Agent": "StockholmApartmentFinder/1.0 (personal project)"},
                timeout=8,
            )
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
            break
        except Exception as e:
            logger.warning(f"Overpass request failed for {url}: {e}")
            last_exc = e
            continue

    if elements is None:
        logger.warning(f"All Overpass mirrors failed. Last error: {last_exc}")
        return _get_pois_google(lat, lng, radius_m)

    supermarkets = []
    parks = []
    gyms = []

    for el in elements:
        # Nodes have direct lat/lng; ways/relations have a centroid if we add out center
        el_lat = el.get("lat") or (el.get("center") or {}).get("lat")
        el_lng = el.get("lon") or (el.get("center") or {}).get("lon")
        if not el_lat or not el_lng:
            continue

        name = el.get("tags", {}).get("name", "")
        dist = _haversine_m(lat, lng, el_lat, el_lng)
        entry = {"name": name, "lat": el_lat,
                 "lng": el_lng, "distance_m": dist}

        tags = el.get("tags", {})
        shop = tags.get("shop", "")
        leisure = tags.get("leisure", "")

        if shop in ("supermarket", "convenience"):
            supermarkets.append(entry)
        elif leisure in ("park", "garden", "nature_reserve"):
            parks.append(entry)
        elif leisure in ("fitness_centre", "sports_centre"):
            gyms.append(entry)

    # Sort each category by distance, keep top 10
    supermarkets.sort(key=lambda x: x["distance_m"])
    parks.sort(key=lambda x: x["distance_m"])
    gyms.sort(key=lambda x: x["distance_m"])

    return {
        "supermarkets": supermarkets[:10],
        "parks": parks[:10],
        "gyms": gyms[:10],
    }


def _get_pois_google(lat: float, lng: float, radius_m: int = 1000) -> dict | None:
    """
    Fallback POI lookup using Google Places Nearby Search API.
    Used when all Overpass mirrors are unavailable.
    """
    try:
        from config import GOOGLE_MAPS_API_KEY
    except ImportError:
        return None
    if not GOOGLE_MAPS_API_KEY:
        return None

    base = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    category_types = {
        "supermarkets": "supermarket",
        "parks": "park",
        "gyms": "gym",
    }
    results = {"supermarkets": [], "parks": [], "gyms": []}

    for key, place_type in category_types.items():
        try:
            resp = requests.get(
                base,
                params={
                    "location": f"{lat},{lng}",
                    "radius": radius_m,
                    "type": place_type,
                    "key": GOOGLE_MAPS_API_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") in ("OK", "ZERO_RESULTS"):
                for place in data.get("results", [])[:10]:
                    plat = place["geometry"]["location"]["lat"]
                    plng = place["geometry"]["location"]["lng"]
                    dist = _haversine_m(lat, lng, plat, plng)
                    results[key].append({
                        "name": place.get("name", ""),
                        "lat": plat,
                        "lng": plng,
                        "distance_m": dist,
                    })
            else:
                logger.warning(
                    f"Google Places returned status '{data.get('status')}' for {place_type}")
        except Exception as e:
            logger.warning(
                f"Google Places request failed for {place_type}: {e}")

    for key in results:
        results[key].sort(key=lambda x: x["distance_m"])

    counts = {k: len(v) for k, v in results.items()}
    logger.info(f"Google Places fallback POIs: {counts}")
    return results


def _build_query(lat: float, lng: float, radius_m: int) -> str:
    """Build an Overpass QL query for POIs around a point."""
    around = f"around:{radius_m},{lat},{lng}"
    return f"""
[out:json][timeout:25];
(
  node["shop"="supermarket"]({around});
  node["shop"="convenience"]({around});
  node["leisure"="park"]({around});
  way["leisure"="park"]({around});
  node["leisure"="garden"]({around});
  way["leisure"="garden"]({around});
  node["leisure"="nature_reserve"]({around});
  way["leisure"="nature_reserve"]({around});
  node["leisure"="fitness_centre"]({around});
  node["leisure"="sports_centre"]({around});
);
out center body;
""".strip()


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * \
        math.cos(phi2) * math.sin(dlam / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)))
