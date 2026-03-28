"""
Trafiklab SL transit service.

Uses two Trafiklab API products:
- ResRobot v2.1 (TRAFIKLAB_RESROBOT_KEY): journey planning + nearby stops lookup
  Bronze tier: 25,000 req/30d — reasonable for personal use.
- Stops data API (TRAFIKLAB_STOPS_KEY): static stop data, only used if ResRobot unavailable.
  Bronze tier: 50 req/30d — extremely limited, results are cached in DB.

Primary approach: ResRobot for everything (ample quota, real-time data).
"""
import logging
import math

import requests

from config import TRAFIKLAB_RESROBOT_KEY, TRAFIKLAB_STOPS_KEY  # noqa: F401

logger = logging.getLogger(__name__)

_RESROBOT_BASE = "https://api.resrobot.se/v2.1"


def get_commute(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict | None:
    """
    Calculate commute from listing to work address via ResRobot.

    Returns:
        {
            "minutes": int,
            "changes": int,
            "lines": ["Tunnelbana 13", "Bus 4"],
            "legs": [{"mode": "METRO", "line": "T13", "from": "...", "to": "..."}],
        }
        or None if unavailable.
    """
    if not TRAFIKLAB_RESROBOT_KEY:
        logger.warning(
            "TRAFIKLAB_RESROBOT_KEY not set — skipping commute calculation")
        return None

    dep_date, dep_time_str = _next_weekday_8am_sthlm()

    try:
        params = {
            "originCoordLat": from_lat,
            "originCoordLong": from_lng,
            "destCoordLat": to_lat,
            "destCoordLong": to_lng,
            "accessId": TRAFIKLAB_RESROBOT_KEY,
            "format": "json",
            "numF": 3,          # fetch 3 options, pick best
            "passlist": 0,
        }
        if dep_date:
            params["date"] = dep_date
            params["time"] = dep_time_str
        resp = requests.get(
            f"{_RESROBOT_BASE}/trip",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"ResRobot trip request failed: {e}")
        return None

    trips = data.get("Trip", [])
    if not trips:
        logger.info("ResRobot returned no trip options")
        return None

    # Pick the trip with fewest minutes (first result is usually best)
    best = trips[0]
    duration_sec = int(best.get("dur", 0))
    minutes = round(duration_sec / 60)
    changes = int(best.get("chg", 0))

    legs_raw = best.get("Leg", [])
    if isinstance(legs_raw, dict):
        legs_raw = [legs_raw]  # single leg comes as dict

    lines = []
    legs = []
    for leg in legs_raw:
        mode = leg.get("type", "").upper()
        # Skip walking legs at start/end
        if mode in ("WALK", "TRANSFER"):
            continue
        name = leg.get("name", "")
        line_num = leg.get("number", "")
        display = name or line_num
        if display and display not in lines:
            lines.append(display)
        origin = leg.get("Origin", {})
        dest = leg.get("Destination", {})
        legs.append({
            "mode": mode,
            "line": display,
            "from": origin.get("name", ""),
            "to": dest.get("name", ""),
            "dep": origin.get("time", ""),
            "arr": dest.get("time", ""),
        })

    return {
        "minutes": minutes,
        "changes": changes,
        "lines": lines,
        "legs": legs,
    }


def get_nearby_stops(lat: float, lng: float, max_results: int = 5) -> list[dict]:
    """
    Find nearby SL transit stops using ResRobot location.nearbystops.

    Returns list of:
        {"name": str, "distance_m": int, "walk_min": int, "products": int}

    Results should be cached in Listing.nearby_stops — TRAFIKLAB_STOPS_KEY has
    only 50 req/30d on Bronze, but ResRobot nearby stops uses TRAFIKLAB_RESROBOT_KEY
    (25k req/30d) which is much more usable.
    """
    if not TRAFIKLAB_RESROBOT_KEY:
        logger.warning(
            "TRAFIKLAB_RESROBOT_KEY not set — skipping nearby stops lookup")
        return []

    try:
        resp = requests.get(
            f"{_RESROBOT_BASE}/location.nearbystops",
            params={
                "originCoordLat": lat,
                "originCoordLong": lng,
                "accessId": TRAFIKLAB_RESROBOT_KEY,
                "format": "json",
                "maxNo": max_results,
                "r": 1000,  # 1 km radius
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"ResRobot nearbystops request failed: {e}")
        return []

    stops = []
    for stop in data.get("StopLocation", []):
        dist_m = int(stop.get("dist", 0))
        walk_min = max(1, round(dist_m / 80))  # ~80 m/min walking speed
        stops.append({
            "name": stop.get("name", ""),
            "distance_m": dist_m,
            "walk_min": walk_min,
            # bitmask: metro/bus/commuter rail
            "products": stop.get("products", 0),
        })
    return stops


def _next_weekday_8am_sthlm():
    """Return (date_str, time_str) tuple for next Mon–Fri at 08:00 Stockholm time (CET/CEST)."""
    import datetime
    now_utc = datetime.datetime.utcnow()
    year = now_utc.year
    mar31 = datetime.datetime(year, 3, 31)
    dst_start = mar31 - datetime.timedelta(days=(mar31.weekday() + 1) % 7)
    oct31 = datetime.datetime(year, 10, 31)
    dst_end = oct31 - datetime.timedelta(days=(oct31.weekday() + 1) % 7)
    utc_offset = 2 if dst_start <= now_utc < dst_end else 1
    sthlm_now = now_utc + datetime.timedelta(hours=utc_offset)
    for days_ahead in range(7):
        candidate = sthlm_now + datetime.timedelta(days=days_ahead)
        if candidate.weekday() < 5:
            target = candidate.replace(
                hour=8, minute=0, second=0, microsecond=0)
            if target > sthlm_now:
                return target.strftime("%Y-%m-%d"), "08:00:00"
    return None, None


def _next_weekday_8am_unix() -> int | None:
    """Return Unix timestamp for next Mon–Fri at 08:00 Stockholm time (CET/CEST)."""
    import datetime
    now_utc = datetime.datetime.utcnow()
    year = now_utc.year
    mar31 = datetime.datetime(year, 3, 31)
    dst_start = mar31 - datetime.timedelta(days=(mar31.weekday() + 1) % 7)
    oct31 = datetime.datetime(year, 10, 31)
    dst_end = oct31 - datetime.timedelta(days=(oct31.weekday() + 1) % 7)
    utc_offset = 2 if dst_start <= now_utc < dst_end else 1
    sthlm_now = now_utc + datetime.timedelta(hours=utc_offset)
    for days_ahead in range(7):
        candidate = sthlm_now + datetime.timedelta(days=days_ahead)
        if candidate.weekday() < 5:
            target = candidate.replace(
                hour=8, minute=0, second=0, microsecond=0)
            if target > sthlm_now:
                target_utc = target - datetime.timedelta(hours=utc_offset)
                epoch = datetime.datetime(1970, 1, 1)
                return int((target_utc - epoch).total_seconds())
    return None


def get_commute_google(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict | None:
    """
    Calculate commute using Google Maps Directions API (transit mode).
    Used as fallback when TRAFIKLAB_RESROBOT_KEY is not set.
    Always uses next weekday 08:00 Stockholm time for consistent morning results.

    Returns same shape as get_commute():
        {"minutes": int, "changes": int, "lines": [...], "legs": [...]}
        or None on failure.
    """
    from config import GOOGLE_MAPS_API_KEY
    if not GOOGLE_MAPS_API_KEY:
        return None

    params = {
        "origin": f"{from_lat},{from_lng}",
        "destination": f"{to_lat},{to_lng}",
        "mode": "transit",
        "key": GOOGLE_MAPS_API_KEY,
    }
    dep_time = _next_weekday_8am_unix()
    if dep_time:
        params["departure_time"] = dep_time

    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"Google Directions commute request failed: {e}")
        return None

    if data.get("status") != "OK" or not data.get("routes"):
        logger.info(
            f"Google Directions returned status '{data.get('status')}' — no commute")
        return None

    leg = data["routes"][0]["legs"][0]
    minutes = round(leg["duration"]["value"] / 60)

    lines = []
    legs = []
    changes = -1  # count transit segments minus 1
    for step in leg.get("steps", []):
        mode = step.get("travel_mode", "WALKING")
        if mode == "TRANSIT":
            changes += 1
            td = step.get("transit_details", {})
            line_info = td.get("line", {})
            line_name = line_info.get(
                "short_name") or line_info.get("name", "")
            vehicle = line_info.get("vehicle", {}).get("type", "BUS")
            dep = td.get("departure_stop", {}).get("name", "")
            arr = td.get("arrival_stop", {}).get("name", "")
            display = line_name or vehicle
            if display and display not in lines:
                lines.append(display)
            legs.append({
                "mode": vehicle,
                "line": display,
                "from": dep,
                "to": arr,
                "dep": "",
                "arr": "",
            })
        elif mode == "WALKING" and legs:
            dur_min = round(step["duration"]["value"] / 60)
            if dur_min >= 2:
                legs.append({
                    "mode": "WALK",
                    "line": "",
                    "from": "",
                    "to": f"Walk {dur_min} min",
                    "dep": "",
                    "arr": "",
                })

    return {
        "minutes": minutes,
        "changes": max(0, changes),
        "lines": lines,
        "legs": legs,
    }


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """Straight-line distance between two lat/lng points, in metres."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * \
        math.cos(phi2) * math.sin(dlam / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)))
