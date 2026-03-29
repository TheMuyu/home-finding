import logging

from flask import Blueprint, current_app, jsonify, request

from database.db import db
from database.models import Listing

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/listings", methods=["GET"])
def get_listings():
    query = Listing.query

    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_rooms = request.args.get("min_rooms", type=int)
    max_rooms = request.args.get("max_rooms", type=int)
    district = request.args.get("district", "").strip()
    saved_only = request.args.get(
        "saved_only", "").lower() in ("1", "true", "yes")
    applied_only = request.args.get(
        "applied_only", "").lower() in ("1", "true", "yes")
    sort = request.args.get("sort", "newest")

    if min_price is not None:
        query = query.filter(Listing.price_sek >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price_sek <= max_price)
    if min_rooms is not None:
        query = query.filter(Listing.rooms >= min_rooms)
    if max_rooms is not None:
        query = query.filter(Listing.rooms <= max_rooms)
    if district:
        query = query.filter(Listing.district.ilike(f"%{district}%"))
    if saved_only:
        query = query.filter(Listing.is_saved == True)  # noqa: E712
    if applied_only:
        query = query.filter(Listing.application_status != "not_applied",
                             Listing.application_status.isnot(None))

    sort_options = {
        "newest": Listing.created_at.desc(),
        "oldest": Listing.created_at.asc(),
        "price_asc": Listing.price_sek.asc(),
        "price_desc": Listing.price_sek.desc(),
        "score": Listing.ai_score.desc(),
        "commute": Listing.commute_minutes.asc(),
    }
    query = query.order_by(sort_options.get(sort, Listing.created_at.desc()))

    listings = query.all()
    return jsonify([l.to_dict() for l in listings])


@api_bp.route("/map-data", methods=["GET"])
def map_data():
    listings = Listing.query.filter(
        Listing.lat.isnot(None), Listing.lng.isnot(None)
    ).all()

    features = []
    for listing in listings:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [listing.lng, listing.lat],
            },
            "properties": {
                "id": listing.id,
                "title": listing.title,
                "price_sek": listing.price_sek,
                "rooms": listing.rooms,
                "district": listing.district,
                "ai_score": listing.ai_score,
                "commute_minutes": listing.commute_minutes,
                "is_saved": listing.is_saved,
                "application_status": listing.application_status,
            },
        })

    return jsonify({"type": "FeatureCollection", "features": features})


@api_bp.route("/enrich/<int:listing_id>", methods=["POST"])
def enrich_listing(listing_id):
    """Synchronously enrich a single listing and return what changed."""
    listing = Listing.query.get_or_404(listing_id)
    try:
        from services.enrichment import enrich_listing_sync
        summary = enrich_listing_sync(
            current_app._get_current_object(), listing_id)
        listing = Listing.query.get(listing_id)
        return jsonify({
            "success": True,
            "enriched": summary,
            "listing": listing.to_dict(),
        })
    except Exception as e:
        logger.error(f"Enrich endpoint failed for listing {listing_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/enrich-all", methods=["POST"])
def enrich_all_listings():
    """Kick off background enrichment for all unenriched listings."""
    try:
        from services.enrichment import enrich_all_async
        enrich_all_async(current_app._get_current_object())
        unenriched_count = Listing.query.filter(
            db.or_(Listing.lat.is_(None), Listing.commute_minutes.is_(None))
        ).count()
        return jsonify({
            "success": True,
            "message": f"Enrichment started for up to {unenriched_count} listings in background.",
            "queued": unenriched_count,
        })
    except Exception as e:
        logger.error(f"Enrich-all endpoint failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/score/<int:listing_id>", methods=["POST"])
def score_listing(listing_id):
    """Score a single listing with Claude AI."""
    from config import ANTHROPIC_API_KEY
    if not ANTHROPIC_API_KEY:
        return jsonify({"success": False, "error": "ANTHROPIC_API_KEY not configured"}), 400

    Listing.query.get_or_404(listing_id)
    try:
        from services.ai_scorer import score_listing_sync
        result = score_listing_sync(
            current_app._get_current_object(), listing_id)
        listing = Listing.query.get(listing_id)
        return jsonify({**result, "listing": listing.to_dict()})
    except Exception as e:
        logger.error(f"Score endpoint failed for listing {listing_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/score-all", methods=["POST"])
def score_all_listings():
    """Kick off background AI scoring for all unscored listings."""
    from config import ANTHROPIC_API_KEY
    if not ANTHROPIC_API_KEY:
        return jsonify({"success": False, "error": "ANTHROPIC_API_KEY not configured"}), 400

    try:
        from services.ai_scorer import score_all_async
        unscored_count = Listing.query.filter(
            Listing.ai_score.is_(None)).count()
        if unscored_count == 0:
            return jsonify({"success": True, "message": "All listings already scored.", "queued": 0})
        score_all_async(current_app._get_current_object())
        return jsonify({
            "success": True,
            "message": f"Scoring {unscored_count} listing(s) in background.",
            "queued": unscored_count,
        })
    except Exception as e:
        logger.error(f"Score-all endpoint failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/districts/recommend", methods=["POST"])
def recommend_districts():
    """Ask Claude AI for the top 3 Stockholm districts based on user preferences."""
    from config import ANTHROPIC_API_KEY
    if not ANTHROPIC_API_KEY:
        return jsonify({"success": False, "error": "ANTHROPIC_API_KEY not configured"}), 400

    try:
        import json as _json
        import re

        import anthropic

        from database.models import UserSettings
        from services.district_advisor import get_all_districts

        settings = UserSettings.query.first()
        districts = get_all_districts()

        settings_lines = []
        if settings:
            settings_lines = [
                f"- Budget: {settings.budget_min}–{settings.budget_max} SEK/month",
                f"- Rooms: {settings.min_rooms}–{settings.max_rooms}",
                f"- Max commute: {settings.max_commute_minutes} minutes",
                f"- Must have washing machine: {settings.must_have_washing_machine}",
                f"- Must have dryer: {settings.must_have_dryer}",
                f"- Must have dishwasher: {settings.must_have_dishwasher}",
                f"- Already preferred: {', '.join(settings.preferred_districts or []) or 'None specified'}",
            ]
        settings_text = "\n".join(
            settings_lines) if settings_lines else "No preferences set."

        districts_text = "\n".join([
            f"- {d['name']}: {d['description']} "
            f"Avg rent: {d['avg_price_range']} SEK/mo. "
            f"Green score: {d['green_score']}/10. "
            f"Safety: {d['safety_note']} "
            f"Transit: {', '.join(d['sl_lines'])}."
            for d in districts
        ])

        prompt = f"""Based on these user preferences, recommend the top 3 Stockholm districts for apartment hunting.

User preferences:
{settings_text}

Available districts:
{districts_text}

Return only valid JSON in this exact format:
{{
  "recommendations": [
    {{"district": "Name", "reason": "Why this suits the user in 1-2 sentences", "fit_score": 9}},
    {{"district": "Name", "reason": "Why this suits the user in 1-2 sentences", "fit_score": 7}},
    {{"district": "Name", "reason": "Why this suits the user in 1-2 sentences", "fit_score": 6}}
  ],
  "summary": "One sentence overall recommendation"
}}"""

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        try:
            result = _json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                result = _json.loads(match.group())
            else:
                return jsonify({"success": False, "error": "Could not parse AI response"}), 500

        return jsonify({"success": True, **result})

    except Exception as e:
        logger.error(f"District recommendation failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/export/csv", methods=["GET"])
def export_csv():
    """Download listings as a CSV file. Pass ?saved_only=1 to export saved listings only."""
    import csv
    import io
    from flask import Response

    saved_only = request.args.get(
        "saved_only", "").lower() in ("1", "true", "yes")
    query = Listing.query
    if saved_only:
        query = query.filter(Listing.is_saved == True)  # noqa: E712
    listings = query.order_by(Listing.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Title", "Address", "District", "Price (SEK/mo)", "Rooms", "Size (m²)",
        "AI Score", "Commute (min)", "Application Status", "Application Date",
        "Available From", "Saved", "Notes", "URL",
    ])
    for lst in listings:
        writer.writerow([
            lst.title,
            lst.address or "",
            lst.district or "",
            lst.price_sek,
            lst.rooms,
            lst.size_sqm if lst.size_sqm is not None else "",
            lst.ai_score if lst.ai_score is not None else "",
            lst.commute_minutes if lst.commute_minutes is not None else "",
            lst.application_status or "",
            lst.application_date.isoformat() if lst.application_date else "",
            lst.available_from if lst.available_from else "",
            "Yes" if lst.is_saved else "No",
            lst.notes or "",
            lst.url or "",
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=listings.csv"},
    )


@api_bp.route("/test-google-maps", methods=["GET"])
def test_google_maps():
    """Quick diagnostic: test that GOOGLE_MAPS_API_KEY works for both Geocoding and Directions."""
    from config import GOOGLE_MAPS_API_KEY
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"key_set": False, "error": "GOOGLE_MAPS_API_KEY is not set in .env"})

    import requests as _req
    results = {"key_set": True, "key_prefix": GOOGLE_MAPS_API_KEY[:8] + "…"}

    # Test 1: Geocoding API
    try:
        r = _req.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": "Stockholm, Sweden",
                    "key": GOOGLE_MAPS_API_KEY},
            timeout=10,
        )
        d = r.json()
        results["geocoding"] = {"status": d.get(
            "status"), "ok": d.get("status") == "OK"}
    except Exception as e:
        results["geocoding"] = {"status": "ERROR",
                                "ok": False, "detail": str(e)}

    # Test 2: Directions API
    try:
        r = _req.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params={
                "origin": "59.3293,18.0686",
                "destination": "59.3340,18.0560",
                "mode": "transit",
                "key": GOOGLE_MAPS_API_KEY,
            },
            timeout=10,
        )
        d = r.json()
        results["directions"] = {"status": d.get(
            "status"), "ok": d.get("status") in ("OK", "ZERO_RESULTS")}
        if d.get("error_message"):
            results["directions"]["detail"] = d["error_message"]
    except Exception as e:
        results["directions"] = {
            "status": "ERROR", "ok": False, "detail": str(e)}

    results["all_ok"] = all(
        v.get("ok") for k, v in results.items() if isinstance(v, dict) and "ok" in v)
    return jsonify(results)


def _next_weekday_8am_unix():
    """Return Unix timestamp for next Mon–Fri at 08:00 Stockholm time (CET/CEST)."""
    import datetime
    now_utc = datetime.datetime.utcnow()
    year = now_utc.year
    # DST: last Sunday in March → last Sunday in October
    mar31 = datetime.datetime(year, 3, 31)
    dst_start = mar31 - datetime.timedelta(days=(mar31.weekday() + 1) % 7)
    oct31 = datetime.datetime(year, 10, 31)
    dst_end = oct31 - datetime.timedelta(days=(oct31.weekday() + 1) % 7)
    utc_offset = 2 if dst_start <= now_utc < dst_end else 1

    sthlm_now = now_utc + datetime.timedelta(hours=utc_offset)
    for days_ahead in range(7):
        candidate = sthlm_now + datetime.timedelta(days=days_ahead)
        if candidate.weekday() < 5:  # Mon–Fri
            target = candidate.replace(
                hour=8, minute=0, second=0, microsecond=0)
            if target > sthlm_now:
                target_utc = target - datetime.timedelta(hours=utc_offset)
                epoch = datetime.datetime(1970, 1, 1)
                return int((target_utc - epoch).total_seconds())
    return None


@api_bp.route("/transit-route/<int:listing_id>", methods=["GET"])
def transit_route(listing_id):
    """
    Fetch transit route from listing to work address using Google Maps Directions API.
    Results are cached in the DB (transit_route column). Pass ?force=1 to refresh.
    Always uses next weekday 08:00 Stockholm time as departure for consistent results.
    Cached routes are served from DB even without an API key or internet connection.
    """
    listing = Listing.query.get_or_404(listing_id)
    if not listing.lat or not listing.lng:
        return jsonify({"success": False, "error": "Listing has no coordinates"}), 400

    from database.models import UserSettings
    settings = UserSettings.query.first()
    if not settings or not settings.work_lat or not settings.work_lng:
        return jsonify({"success": False, "error": "Work address not set in Settings"}), 400

    # Return cached route unless force-refresh requested — no API key needed for cache
    force = request.args.get("force", "").lower() in ("1", "true")
    if listing.transit_route and not force:
        cached = listing.transit_route
        cached["work_lat"] = settings.work_lat
        cached["work_lng"] = settings.work_lng
        return jsonify({"success": True, **cached})

    # No cache (or force refresh) — need to call Google Maps API
    from config import GOOGLE_MAPS_API_KEY
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"success": False, "error": "GOOGLE_MAPS_API_KEY not configured"}), 400

    import requests as _requests
    try:
        params = {
            "origin": f"{listing.lat},{listing.lng}",
            "destination": f"{settings.work_lat},{settings.work_lng}",
            "mode": "transit",
            "key": GOOGLE_MAPS_API_KEY,
        }
        dep_time = _next_weekday_8am_unix()
        if dep_time:
            params["departure_time"] = dep_time

        resp = _requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK" or not data.get("routes"):
            return jsonify({
                "success": False,
                "error": f"Directions API: {data.get('status', 'no routes')}",
            }), 400

        route = data["routes"][0]
        leg = route["legs"][0]

        steps = []
        for step in leg.get("steps", []):
            mode = step.get("travel_mode", "WALKING")
            entry = {
                "mode": mode,
                "polyline": step["polyline"]["points"],
                "duration_min": round(step["duration"]["value"] / 60),
                "distance_m": step["distance"]["value"],
            }
            if mode == "TRANSIT":
                td = step.get("transit_details", {})
                line = td.get("line", {})
                entry["line_name"] = line.get(
                    "short_name") or line.get("name", "")
                entry["vehicle"] = line.get("vehicle", {}).get("type", "BUS")
                entry["departure_stop"] = td.get(
                    "departure_stop", {}).get("name", "")
                entry["arrival_stop"] = td.get(
                    "arrival_stop", {}).get("name", "")
            steps.append(entry)

        total_min = round(leg["duration"]["value"] / 60)
        result = {
            "steps": steps,
            "total_minutes": total_min,
            "summary": route.get("summary", ""),
        }

        # Cache in DB; also backfill commute_minutes if missing
        listing.transit_route = result
        if not listing.commute_minutes:
            listing.commute_minutes = total_min
        db.session.commit()

        result["work_lat"] = settings.work_lat
        result["work_lng"] = settings.work_lng
        return jsonify({"success": True, **result})

    except Exception as e:
        logger.error(f"Transit route failed for listing {listing_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/seed", methods=["POST"])
def run_seed():
    try:
        from seed_data import seed_listings
        count = seed_listings()
        return jsonify({"success": True, "message": f"Seeded {count} listings.", "count": count})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_bp.route("/clear-seed", methods=["POST"])
def run_clear_seed():
    try:
        from seed_data import clear_seed_data
        count = clear_seed_data()
        return jsonify({"success": True, "message": f"Removed {count} seed listings.", "count": count})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
