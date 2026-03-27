from datetime import date
from flask import Blueprint, render_template, request, jsonify, abort
from database.db import db
from database.models import Listing

listings_bp = Blueprint("listings", __name__, url_prefix="/")

VALID_STATUSES = ("not_applied", "applied", "waiting", "rejected", "accepted")


@listings_bp.route("/")
def index():
    listings = Listing.query.order_by(Listing.created_at.desc()).all()
    listings_json = [l.to_dict() for l in listings]
    return render_template("index.html", listings=listings, listings_json=listings_json)


@listings_bp.route("/listings/<int:listing_id>", methods=["GET"])
def get_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    return jsonify(listing.to_dict())


@listings_bp.route("/listings/<int:listing_id>/save", methods=["POST"])
def toggle_save(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.is_saved = not listing.is_saved
    db.session.commit()
    return jsonify({"id": listing.id, "is_saved": listing.is_saved})


@listings_bp.route("/listings/<int:listing_id>/status", methods=["POST"])
def update_status(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    data = request.get_json(silent=True) or {}
    status = data.get("application_status")
    if status not in VALID_STATUSES:
        abort(400, description=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
    listing.application_status = status
    if status == "applied" and not listing.application_date:
        listing.application_date = date.today()
    db.session.commit()
    return jsonify({"id": listing.id, "application_status": listing.application_status,
                    "application_date": listing.application_date.isoformat() if listing.application_date else None})


@listings_bp.route("/listings/<int:listing_id>/notes", methods=["POST"])
def update_notes(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    data = request.get_json(silent=True) or {}
    listing.notes = data.get("notes", "")
    db.session.commit()
    return jsonify({"id": listing.id, "notes": listing.notes})
