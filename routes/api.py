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
    saved_only = request.args.get("saved_only", "").lower() in ("1", "true", "yes")
    applied_only = request.args.get("applied_only", "").lower() in ("1", "true", "yes")
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
        summary = enrich_listing_sync(current_app._get_current_object(), listing_id)
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
        result = score_listing_sync(current_app._get_current_object(), listing_id)
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
        unscored_count = Listing.query.filter(Listing.ai_score.is_(None)).count()
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
