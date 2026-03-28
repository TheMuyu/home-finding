from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import db
from database.models import UserSettings

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


def get_or_create_settings():
    """Get existing settings or create default settings row."""
    settings = UserSettings.query.get(1)
    if not settings:
        settings = UserSettings(
            id=1,
            work_address="",
            budget_min=5000,
            budget_max=25000,
            min_rooms=1,
            max_rooms=3,
            max_commute_minutes=45,
            must_have_washing_machine=False,
            must_have_dryer=False,
            must_have_dishwasher=False,
            preferred_districts=[],
            theme="light",
        )
        db.session.add(settings)
        db.session.commit()
    return settings


@settings_bp.route("/", methods=["GET"])
def settings_page():
    settings = get_or_create_settings()
    return render_template("settings.html", settings=settings)


@settings_bp.route("/", methods=["POST"])
def save_settings():
    settings = get_or_create_settings()

    settings.work_address = request.form.get("work_address", "").strip()
    settings.budget_min = int(request.form.get("budget_min", 5000) or 5000)
    settings.budget_max = int(request.form.get("budget_max", 25000) or 25000)
    settings.min_rooms = int(request.form.get("min_rooms", 1) or 1)
    settings.max_rooms = int(request.form.get("max_rooms", 3) or 3)
    settings.max_commute_minutes = int(request.form.get("max_commute_minutes", 45) or 45)

    floor_min_raw = request.form.get("floor_min", "").strip()
    settings.floor_min = int(floor_min_raw) if floor_min_raw else None

    settings.must_have_washing_machine = "must_have_washing_machine" in request.form
    settings.must_have_dryer = "must_have_dryer" in request.form
    settings.must_have_dishwasher = "must_have_dishwasher" in request.form

    preferred_districts = request.form.getlist("preferred_districts")
    settings.preferred_districts = preferred_districts

    settings.theme = request.form.get("theme", "light")

    # Geocode work address (cache means re-saves are fast; clear coords if address changes)
    if settings.work_address:
        try:
            from services.maps import geocode_address
            result = geocode_address(settings.work_address)
            if result:
                settings.work_lat = result["lat"]
                settings.work_lng = result["lng"]
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not geocode work address: {e}")
    else:
        settings.work_lat = None
        settings.work_lng = None

    db.session.commit()
    flash("Settings saved successfully.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/api/current", methods=["GET"])
def api_current_settings():
    settings = get_or_create_settings()
    return jsonify(settings.to_dict())


@settings_bp.route("/api/theme", methods=["POST"])
def update_theme():
    """Persist theme toggle to DB (called by the navbar toggle button)."""
    data = request.get_json(silent=True) or {}
    theme = data.get("theme", "light")
    if theme not in ("light", "dark"):
        return jsonify({"error": "Invalid theme"}), 400
    settings = get_or_create_settings()
    settings.theme = theme
    db.session.commit()
    return jsonify({"theme": theme})
