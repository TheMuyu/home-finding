from flask import Blueprint, jsonify, request
from database.db import db
from database.models import Listing

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
