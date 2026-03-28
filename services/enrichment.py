"""
Listing enrichment runner.

Geocodes addresses, calculates commute times, fetches nearby transit stops
and POIs for listings that haven't been enriched yet.

Enrichment runs in a background thread so it doesn't block HTTP responses.
Each step is idempotent: already-enriched fields are skipped.
"""
import logging
import threading

from database.db import db
from database.models import Listing, UserSettings

logger = logging.getLogger(__name__)


# ── Public API ──────────────────────────────────────────────────────────────

def enrich_listing_async(app, listing_id: int) -> None:
    """Kick off enrichment for a single listing in a background thread."""
    t = threading.Thread(
        target=_run_enrich_one,
        args=(app, listing_id),
        daemon=True,
    )
    t.start()


def enrich_all_async(app) -> None:
    """Kick off enrichment for all unenriched listings in a background thread."""
    t = threading.Thread(
        target=_run_enrich_all,
        args=(app,),
        daemon=True,
    )
    t.start()


def enrich_listing_sync(app, listing_id: int) -> dict:
    """
    Synchronous enrichment for a single listing.
    Returns a summary dict with what was enriched.
    """
    with app.app_context():
        return _enrich_one(listing_id)


# ── Internal workers ────────────────────────────────────────────────────────

def _run_enrich_one(app, listing_id: int) -> None:
    with app.app_context():
        try:
            _enrich_one(listing_id)
        except Exception as e:
            logger.error(f"Enrichment failed for listing {listing_id}: {e}")


def _run_enrich_all(app) -> None:
    with app.app_context():
        try:
            unenriched = Listing.query.filter(
                db.or_(
                    Listing.lat.is_(None),
                    Listing.commute_minutes.is_(None),
                )
            ).all()
            ids = [l.id for l in unenriched]
            logger.info(f"Starting enrichment for {len(ids)} listings")
            for listing_id in ids:
                try:
                    _enrich_one(listing_id)
                except Exception as e:
                    logger.error(
                        f"Enrichment failed for listing {listing_id}: {e}")
        except Exception as e:
            logger.error(f"Bulk enrichment failed: {e}")


def _enrich_one(listing_id: int) -> dict:
    """
    Enrich a single listing. Skips steps that are already done.
    Returns dict describing what changed.
    """
    from services.maps import geocode_address
    from services.overpass import get_nearby_pois
    from services.transit import get_commute, get_nearby_stops

    summary = {"geocoded": False, "commute": False,
               "stops": False, "pois": False}

    listing = Listing.query.get(listing_id)
    if not listing:
        logger.warning(f"Listing {listing_id} not found for enrichment")
        return summary

    # ── 1. Geocode listing address ──────────────────────────────────────────
    if listing.lat is None or listing.lng is None:
        if listing.address:
            # Append Stockholm for better Nominatim accuracy
            query = listing.address
            if "stockholm" not in query.lower():
                query = f"{query}, Stockholm, Sweden"
            result = geocode_address(query)
            if result:
                listing.lat = result["lat"]
                listing.lng = result["lng"]
                db.session.commit()
                summary["geocoded"] = True
                logger.info(
                    f"Geocoded listing {listing_id}: ({listing.lat}, {listing.lng})")
            else:
                logger.warning(
                    f"Could not geocode address for listing {listing_id}: '{listing.address}'")
        else:
            logger.info(
                f"Listing {listing_id} has no address — skipping geocoding")

    # Need lat/lng for transit and POIs
    if listing.lat is None or listing.lng is None:
        return summary

    # ── 2. Get work address lat/lng ─────────────────────────────────────────
    settings = UserSettings.query.get(1)
    work_lat = settings.work_lat if settings else None
    work_lng = settings.work_lng if settings else None

    # Geocode work address if not already done
    if settings and settings.work_address and (work_lat is None or work_lng is None):
        from services.maps import geocode_address
        result = geocode_address(settings.work_address)
        if result:
            settings.work_lat = result["lat"]
            settings.work_lng = result["lng"]
            db.session.commit()
            work_lat = settings.work_lat
            work_lng = settings.work_lng

    # ── 3. Calculate commute time ───────────────────────────────────────────
    if listing.commute_minutes is None and work_lat and work_lng:
        commute = get_commute(listing.lat, listing.lng, work_lat, work_lng)
        if commute is None:
            from services.transit import get_commute_google
            commute = get_commute_google(
                listing.lat, listing.lng, work_lat, work_lng)
        if commute:
            listing.commute_minutes = commute["minutes"]
            listing.commute_details = {
                "changes": commute["changes"],
                "lines": commute["lines"],
                "legs": commute["legs"],
            }
            db.session.commit()
            summary["commute"] = True
            logger.info(
                f"Commute for listing {listing_id}: {commute['minutes']} min")

    # ── 4. Nearby transit stops ─────────────────────────────────────────────
    if not listing.nearby_stops:
        stops = get_nearby_stops(listing.lat, listing.lng)
        if stops:
            listing.nearby_stops = stops
            db.session.commit()
            summary["stops"] = True
            logger.info(
                f"Found {len(stops)} nearby stops for listing {listing_id}")

    # ── 5. Nearby POIs ──────────────────────────────────────────────────────
    existing_pois = listing.nearby_pois or {}
    if not existing_pois.get("supermarkets") and not existing_pois.get("parks"):
        pois = get_nearby_pois(listing.lat, listing.lng)
        listing.nearby_pois = pois
        db.session.commit()
        summary["pois"] = True
        counts = {k: len(v) for k, v in pois.items()}
        logger.info(f"POIs for listing {listing_id}: {counts}")

    return summary
