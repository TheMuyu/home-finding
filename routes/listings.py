import logging
from datetime import date, datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from database.db import db
from database.models import Listing, UserSettings

logger = logging.getLogger(__name__)

listings_bp = Blueprint("listings", __name__, url_prefix="/")

VALID_STATUSES = ("not_applied", "applied", "waiting", "rejected", "accepted")


# ── Listings index ────────────────────────────────────────────────────────────

@listings_bp.route("/")
def index():
    listings = Listing.query.order_by(Listing.created_at.desc()).all()
    listings_json = [l.to_dict() for l in listings]
    return render_template("index.html", listings=listings, listings_json=listings_json)


# ── Single listing JSON ───────────────────────────────────────────────────────

@listings_bp.route("/listings/<int:listing_id>", methods=["GET"])
def get_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    return jsonify(listing.to_dict())


# ── Save toggle ───────────────────────────────────────────────────────────────

@listings_bp.route("/listings/<int:listing_id>/save", methods=["POST"])
def toggle_save(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.is_saved = not listing.is_saved
    db.session.commit()
    return jsonify({"id": listing.id, "is_saved": listing.is_saved})


# ── Application status ────────────────────────────────────────────────────────

@listings_bp.route("/listings/<int:listing_id>/status", methods=["POST"])
def update_status(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    data = request.get_json(silent=True) or {}
    status = data.get("application_status")
    if status not in VALID_STATUSES:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"}), 400
    listing.application_status = status
    if status == "applied" and not listing.application_date:
        listing.application_date = date.today()
    db.session.commit()
    return jsonify({
        "id": listing.id,
        "application_status": listing.application_status,
        "application_date": listing.application_date.isoformat() if listing.application_date else None,
    })


# ── Notes ─────────────────────────────────────────────────────────────────────

@listings_bp.route("/listings/<int:listing_id>/notes", methods=["POST"])
def update_notes(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    data = request.get_json(silent=True) or {}
    listing.notes = data.get("notes", "")
    db.session.commit()
    return jsonify({"id": listing.id, "notes": listing.notes})


# ── Add listing page (GET) ────────────────────────────────────────────────────

@listings_bp.route("/add-listing", methods=["GET"])
def add_listing_page():
    prefill_url = request.args.get("url", "")
    return render_template("add_listing.html", prefill_url=prefill_url)


# ── Save listing (POST from add_listing form) ─────────────────────────────────

@listings_bp.route("/add-listing", methods=["POST"])
def save_listing():
    import json as _json

    source = request.form.get("source", "manual")
    url = request.form.get("url", "").strip() or None
    title = request.form.get("title", "").strip()
    address = request.form.get("address", "").strip()
    district = request.form.get("district", "").strip()
    description = request.form.get("description", "").strip()

    # Required numeric fields with safe fallbacks
    try:
        price_sek = int(request.form.get("price_sek") or 0)
    except (TypeError, ValueError):
        price_sek = 0
    try:
        rooms = int(request.form.get("rooms") or 1)
    except (TypeError, ValueError):
        rooms = 1
    try:
        floor = int(request.form.get("floor")) if request.form.get("floor") else None
    except (TypeError, ValueError):
        floor = None
    try:
        size_sqm = int(request.form.get("size_sqm")) if request.form.get("size_sqm") else None
    except (TypeError, ValueError):
        size_sqm = None

    # Available from date
    available_from = None
    available_from_str = request.form.get("available_from", "").strip()
    if available_from_str:
        try:
            available_from = datetime.strptime(available_from_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    available_until = request.form.get("available_until", "").strip() or None

    # Amenities — collected from individual amenity_X checkboxes
    all_amenity_keys = [
        "balcony", "rooftop_terrace", "garden", "sauna", "pool",
        "fridge", "freezer", "microwave", "oven", "stove",
        "dishwasher", "washing_machine", "tumble_dryer",
        "shower", "bathtub", "toilet",
        "elevator", "storage_room", "parking", "bike_storage",
        "internet", "television",
    ]
    amenities = [k for k in all_amenity_keys if f"amenity_{k}" in request.form]
    # Also merge any pre-set amenities_json (from URL extraction hidden field)
    amenities_json_str = request.form.get("amenities_json", "").strip()
    if amenities_json_str:
        try:
            from_json = _json.loads(amenities_json_str)
            if isinstance(from_json, list):
                for k in from_json:
                    if k not in amenities:
                        amenities.append(k)
        except (ValueError, TypeError):
            pass
    has_washing_machine = "washing_machine" in amenities
    has_dryer           = "tumble_dryer"    in amenities
    has_dishwasher      = "dishwasher"      in amenities

    # Listing character
    home_type = request.form.get("home_type", "").strip() or None
    furnishing = request.form.get("furnishing", "").strip() or None
    is_shared_str = request.form.get("is_shared", "")
    is_shared = True if is_shared_str == "true" else (False if is_shared_str == "false" else None)

    # Rent breakdown
    try:
        service_fee_sek = int(request.form.get("service_fee_sek") or 0) or None
    except (TypeError, ValueError):
        service_fee_sek = None
    electricity_included = (
        True if request.form.get("electricity_included") == "true"
        else False if request.form.get("electricity_included") == "false"
        else None
    )
    try:
        deposit_months = int(request.form.get("deposit_months") or 0) or None
    except (TypeError, ValueError):
        deposit_months = None

    # House rules (JSON from hidden field)
    house_rules = {}
    house_rules_str = request.form.get("house_rules_json", "").strip()
    if house_rules_str:
        try:
            house_rules = _json.loads(house_rules_str)
            if not isinstance(house_rules, dict):
                house_rules = {}
        except (ValueError, TypeError):
            house_rules = {}

    # Images (JSON array from hidden field, populated by JS on URL extract)
    images = []
    images_json_str = request.form.get("images_json", "").strip()
    if images_json_str:
        try:
            images = _json.loads(images_json_str)
            if not isinstance(images, list):
                images = []
        except (ValueError, TypeError):
            images = []

    if not title:
        flash("Title is required.", "error")
        return redirect(url_for("listings.add_listing_page"))

    listing = Listing(
        source=source,
        url=url,
        title=title,
        address=address,
        district=district,
        description=description,
        price_sek=price_sek,
        rooms=rooms,
        floor=floor,
        size_sqm=size_sqm,
        available_from=available_from,
        available_until=available_until,
        amenities=amenities,
        has_washing_machine=has_washing_machine,
        has_dryer=has_dryer,
        has_dishwasher=has_dishwasher,
        home_type=home_type,
        furnishing=furnishing,
        is_shared=is_shared,
        service_fee_sek=service_fee_sek,
        electricity_included=electricity_included,
        deposit_months=deposit_months,
        house_rules=house_rules,
        images=images,
    )

    db.session.add(listing)
    try:
        db.session.commit()
        # Enrich in background (geocode, commute, POIs)
        try:
            from flask import current_app
            from services.enrichment import enrich_listing_async
            enrich_listing_async(current_app._get_current_object(), listing.id)
        except Exception as e:
            logger.warning(f"Could not start enrichment for listing {listing.id}: {e}")
        flash("Listing saved successfully!", "success")
        return redirect(url_for("listings.index"))
    except IntegrityError:
        db.session.rollback()
        flash("A listing with this URL already exists.", "error")
        return redirect(url_for("listings.add_listing_page"))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to save listing: {e}")
        flash("Failed to save listing. Please try again.", "error")
        return redirect(url_for("listings.add_listing_page"))


# ── URL extraction endpoint ────────────────────────────────────────────────────

@listings_bp.route("/listings/extract-url", methods=["POST"])
def extract_url():
    """Extract listing data from a Qasa URL. Returns JSON."""
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400
    if "qasa.se" not in url and "qasa.com" not in url:
        return jsonify({"error": "Only Qasa URLs are supported for extraction"}), 400

    try:
        from scrapers.qasa import extract_from_url
    except ImportError as e:
        return jsonify({"error": f"Scraper not available: {e}"}), 503

    result = extract_from_url(url)
    if result is None:
        return jsonify({"error": "Could not extract listing data from this URL. Try entering manually."}), 422

    return jsonify(result)


# ── URL extraction debug ──────────────────────────────────────────────────────

@listings_bp.route("/listings/debug-url", methods=["POST"])
def debug_url():
    """
    Diagnostic endpoint — returns raw info about what Playwright sees on the page.
    Helps diagnose why extraction fails. Only for development use.
    """
    import json as _json

    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL required"}), 400

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return jsonify({"error": "Playwright not installed"}), 503

    result = {
        "requested_url": url,
        "final_url": None,
        "page_title": None,
        "http_status": None,
        "has_next_data": False,
        "next_data_keys": [],
        "next_data_page_props_keys": [],
        "next_data_snippet": None,
        "extracted_data": None,
        "error": None,
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()

            response = None
            try:
                response = page.goto(url, wait_until="networkidle", timeout=30_000)
            except Exception:
                try:
                    response = page.goto(url, wait_until="domcontentloaded", timeout=20_000)
                    page.wait_for_timeout(3_000)
                except Exception as e:
                    result["error"] = f"Navigation failed: {e}"
                    browser.close()
                    return jsonify(result)

            result["final_url"] = page.url
            result["page_title"] = page.title()
            if response:
                result["http_status"] = response.status

            # Check __NEXT_DATA__
            try:
                next_data_text = page.evaluate(
                    "() => { const el = document.getElementById('__NEXT_DATA__'); return el ? el.textContent : null; }"
                )
                if next_data_text:
                    result["has_next_data"] = True
                    nd = _json.loads(next_data_text)
                    result["next_data_keys"] = list(nd.keys())
                    page_props = nd.get("props", {}).get("pageProps", {})
                    result["next_data_page_props_keys"] = list(page_props.keys())
                    # First 3000 chars of raw JSON to inspect structure
                    result["next_data_snippet"] = next_data_text[:3000]
            except Exception as e:
                result["error"] = f"__NEXT_DATA__ parse error: {e}"

            # Also run full extraction so we can see what came out
            try:
                from scrapers.qasa import _extract_page_data
                result["extracted_data"] = _extract_page_data(page, url)
            except Exception as e:
                result["extracted_data"] = f"extraction error: {e}"

            browser.close()

    except Exception as e:
        result["error"] = str(e)

    return jsonify(result)


# ── Bulk Qasa scrape ──────────────────────────────────────────────────────────

@listings_bp.route("/scrape", methods=["POST"])
def run_scrape():
    """
    Kick off a synchronous Qasa bulk scrape using current user settings as filters.
    Returns JSON with counts: {new, duplicates, errors, total}.
    This may take several minutes depending on how many listings are found.
    """
    try:
        from scrapers.qasa import scrape_qasa
    except ImportError as e:
        return jsonify({"error": f"Scraper not available: {e}"}), 503

    settings = UserSettings.query.first()
    min_price = settings.budget_min if settings else None
    max_price = settings.budget_max if settings else None
    min_rooms = settings.min_rooms if settings else None
    max_rooms = settings.max_rooms if settings else None

    listings_data = scrape_qasa(min_price, max_price, min_rooms, max_rooms)

    new_count = 0
    duplicate_count = 0
    error_count = 0

    for item in listings_data:
        listing = Listing(
            source="qasa",
            url=item.get("url"),
            title=item.get("title", ""),
            description=item.get("description", ""),
            address=item.get("address", ""),
            district=item.get("district", ""),
            lat=item.get("lat"),
            lng=item.get("lng"),
            price_sek=item.get("price_sek") or 0,
            rooms=item.get("rooms") or 1,
            floor=item.get("floor"),
            size_sqm=item.get("size_sqm"),
            available_until=item.get("available_until"),
            amenities=item.get("amenities") or [],
            has_washing_machine=item.get("has_washing_machine", False),
            has_dryer=item.get("has_dryer", False),
            has_dishwasher=item.get("has_dishwasher", False),
            home_type=item.get("home_type"),
            furnishing=item.get("furnishing"),
            is_shared=item.get("is_shared"),
            service_fee_sek=item.get("service_fee_sek"),
            electricity_included=item.get("electricity_included"),
            deposit_months=item.get("deposit_months"),
            house_rules=item.get("house_rules") or {},
            images=item.get("images") or [],
        )
        db.session.add(listing)
        try:
            db.session.commit()
            new_count += 1
        except IntegrityError:
            db.session.rollback()
            duplicate_count += 1
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save scraped listing: {e}")
            error_count += 1

    # Enrich all newly-saved listings in background
    if new_count > 0:
        try:
            from flask import current_app
            from services.enrichment import enrich_all_async
            enrich_all_async(current_app._get_current_object())
        except Exception as e:
            logger.warning(f"Could not start bulk enrichment: {e}")

    return jsonify({
        "new": new_count,
        "duplicates": duplicate_count,
        "errors": error_count,
        "total": len(listings_data),
    })
