"""
Qasa.se scraper — Session 2.

Two main functions:
- extract_from_url(url)  → dict | None   (single listing)
- scrape_qasa(...)       → list[dict]    (bulk search)

Plus:
- parse_amenities(text) → dict          (shared amenity keyword matcher)
"""

import json
import logging
import random
import re
import time

logger = logging.getLogger(__name__)

SEARCH_BASE_URL = "https://qasa.com/se/en/find-home/stockholm"
MAX_LISTINGS = 50
MIN_DELAY = 2.0
MAX_DELAY = 5.0

# All Qasa amenity keys with the text labels that identify them on the page.
# Order matters for multi-word terms — put longer phrases first.
QASA_AMENITIES = [
    ("balcony",           ["balcony", "balkong"]),
    ("rooftop_terrace",   ["rooftop terrace", "takrasterass"]),
    ("garden",            ["garden", "trädgård"]),
    ("sauna",             ["sauna", "bastu"]),
    ("pool",              ["pool"]),
    ("fridge",            ["fridge", "refrigerator", "kylskåp"]),
    ("freezer",           ["freezer", "frys"]),
    ("microwave",         ["microwave oven", "microwave", "mikrovågsugn"]),
    ("oven",              ["oven", "ugn"]),
    ("stove",             ["stove", "spis"]),
    ("dishwasher",        ["dish washer", "dishwasher", "diskmaskin"]),
    ("washing_machine",   ["washing machine",
     "tvättmaskin", "tvättmöjlighet"]),
    ("tumble_dryer",      ["tumble dryer", "torktumlare", "torkskåp"]),
    ("shower",            ["shower", "dusch"]),
    ("bathtub",           ["bathtub", "bath tub", "badkar"]),
    ("toilet",            ["toilet", "toalett"]),
    ("elevator",          ["elevator", "hiss"]),
    ("storage_room",      ["storage room", "förråd"]),
    ("parking",           ["parking available", "parkering"]),
    ("bike_storage",      ["bike storage", "cykelrum", "cykelförråd"]),
    ("internet",          ["internet"]),
    ("television",        ["television"]),
]

# Human-readable labels and categories for display
AMENITY_META = {
    "balcony":          {"label": "Balcony",          "category": "Outdoor"},
    "rooftop_terrace":  {"label": "Rooftop terrace",  "category": "Outdoor"},
    "garden":           {"label": "Garden",            "category": "Outdoor"},
    "sauna":            {"label": "Sauna",             "category": "Standout"},
    "pool":             {"label": "Pool",              "category": "Standout"},
    "fridge":           {"label": "Fridge",            "category": "Kitchen"},
    "freezer":          {"label": "Freezer",           "category": "Kitchen"},
    "microwave":        {"label": "Microwave",         "category": "Kitchen"},
    "oven":             {"label": "Oven",              "category": "Kitchen"},
    "stove":            {"label": "Stove",             "category": "Kitchen"},
    "dishwasher":       {"label": "Dishwasher",        "category": "Kitchen"},
    "washing_machine":  {"label": "Washing machine",   "category": "Washroom"},
    "tumble_dryer":     {"label": "Tumble dryer",      "category": "Washroom"},
    "shower":           {"label": "Shower",            "category": "Bathroom"},
    "bathtub":          {"label": "Bathtub",           "category": "Bathroom"},
    "toilet":           {"label": "Toilet",            "category": "Bathroom"},
    "elevator":         {"label": "Elevator",          "category": "Building"},
    "storage_room":     {"label": "Storage room",      "category": "Building"},
    "parking":          {"label": "Parking",           "category": "Building"},
    "bike_storage":     {"label": "Bike storage",      "category": "Building"},
    "internet":         {"label": "Internet",          "category": "Technology"},
    "television":       {"label": "Television",        "category": "Technology"},
}

# Legacy keyword map for parse_amenities() backward compat
AMENITY_KEYWORDS = {
    "has_washing_machine": ["tvättmaskin", "tvättmöjlighet", "washing machine", "washer"],
    "has_dryer":           ["torktumlare", "torkskåp", "tumble dryer", "dryer"],
    "has_dishwasher":      ["diskmaskin", "dish washer", "dishwasher"],
}


# ── Shared helpers ────────────────────────────────────────────────────────────

def _normalize_image_url(url: str) -> str:
    """Upgrade any Qasa image URL to 1200x1200/smart resolution."""
    return re.sub(r"(https://img\.qasa\.se/unsafe/)\d+x\d+(?:/smart)?", r"\g<1>1200x1200/smart", url)


def parse_amenities(text: str) -> dict:
    """Detect amenities from description/title text by keyword matching."""
    result = {k: False for k in AMENITY_KEYWORDS}
    if not text:
        return result
    text_lower = text.lower()
    for field, keywords in AMENITY_KEYWORDS.items():
        result[field] = any(kw in text_lower for kw in keywords)
    return result


def _random_delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def _parse_price(text: str):
    """Extract a monthly rent in SEK from arbitrary text. Returns int or None."""
    patterns = [
        r"(\d[\d\s\u00a0]*)\s*kr(?:/m[åa]n|/month)?",
        r"(\d[\d\s\u00a0]*)\s*SEK",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = re.sub(r"[\s\u00a0]", "", match.group(1))
            try:
                val = int(raw)
                if 1_000 < val < 200_000:
                    return val
            except ValueError:
                continue
    return None


def _parse_rooms(text: str):
    """Extract room count from text like '2 rum', '3 rooms'. Returns int or None."""
    for pattern in (r"(\d+)\s*rum", r"(\d+)\s*room", r"(\d+)\s*rok"):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            if 1 <= val <= 20:
                return val
    return None


def _parse_size(text: str):
    """Extract size in sqm from text like '65 m²', '65 kvm'. Returns int or None."""
    for pattern in (r"(\d+)\s*m[²2]", r"(\d+)\s*kvm", r"(\d+)\s*sqm"):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            if 10 < val < 500:
                return val
    return None


# ── Next.js __NEXT_DATA__ extraction ─────────────────────────────────────────

def _find_coords_in_tree(obj, depth: int = 0) -> tuple[float, float] | tuple[None, None]:
    """
    Recursively search a JSON tree for the first dict that contains both
    a latitude-like key and a longitude-like key with plausible Stockholm values.
    Returns (lat, lng) or (None, None).
    """
    if depth > 12 or not isinstance(obj, (dict, list)):
        return None, None

    if isinstance(obj, dict):
        # Try direct keys on this dict
        lat = obj.get("latitude") or obj.get("lat")
        lng = obj.get("longitude") or obj.get("lng") or obj.get("lon")
        if lat is not None and lng is not None:
            try:
                lat, lng = float(lat), float(lng)
                # Rough bounding box for Sweden
                if 55.0 < lat < 70.0 and 10.0 < lng < 25.0:
                    return lat, lng
            except (TypeError, ValueError):
                pass
        # Recurse into values
        for v in obj.values():
            lat, lng = _find_coords_in_tree(v, depth + 1)
            if lat is not None:
                return lat, lng
    elif isinstance(obj, list):
        for item in obj:
            lat, lng = _find_coords_in_tree(item, depth + 1)
            if lat is not None:
                return lat, lng

    return None, None


def _extract_from_next_data(next_data: dict, data: dict):
    """Populate data dict from the Next.js __NEXT_DATA__ blob."""
    try:
        page_props = next_data.get("props", {}).get("pageProps", {})

        # Qasa may nest the listing under various keys
        listing = (
            page_props.get("listing")
            or page_props.get("home")
            or page_props.get("apartment")
            or page_props.get("rentalListing")
            or {}
        )

        # Shallow fallback: find any dict that looks like a listing
        if not listing:
            for v in page_props.values():
                if isinstance(v, dict) and ("rent" in v or "price" in v or "title" in v):
                    listing = v
                    break

        if not listing:
            return

        # Title
        data["title"] = (
            listing.get("title")
            or listing.get("name")
            or listing.get("heading")
            or ""
        )

        # Price
        for key in ("rent", "price", "monthlyRent", "rentAmount", "pricePerMonth"):
            val = listing.get(key)
            if isinstance(val, (int, float)) and 1_000 < val < 200_000:
                data["price_sek"] = int(val)
                break

        # Rooms
        for key in ("roomCount", "rooms", "numberOfRooms", "bedroomCount"):
            val = listing.get(key)
            if isinstance(val, (int, float)) and 1 <= val <= 20:
                data["rooms"] = int(val)
                break

        # Size
        for key in ("squareMeters", "size", "area", "livingArea", "sqm"):
            val = listing.get(key)
            if isinstance(val, (int, float)) and 10 < val < 500:
                data["size_sqm"] = int(val)
                break

        # Floor
        for key in ("floor", "floorNumber", "apartmentFloor"):
            val = listing.get(key)
            if isinstance(val, (int, float)):
                data["floor"] = int(val)
                break

        # Available from (moveIn field may be "now" string or ISO date)
        if not data.get("available_from"):
            for key in ("moveIn", "availableFrom", "startDate", "moveInDate"):
                val = listing.get(key)
                if isinstance(val, str) and val:
                    val_lower = val.lower().strip()
                    if val_lower in ("now", "immediately", "asap"):
                        data["available_from"] = "now"
                    else:
                        # keep YYYY-MM-DD part
                        data["available_from"] = val_lower[:10]
                    break

        # Available until
        if not data.get("available_until"):
            for key in ("moveOut", "endDate", "availableTo", "availableUntil", "moveOutDate"):
                val = listing.get(key)
                if isinstance(val, str) and val:
                    val_lower = val.lower().strip()
                    if "further" in val_lower or "notice" in val_lower:
                        data["available_until"] = "until_further_notice"
                    else:
                        data["available_until"] = val_lower[:10]
                    break

        # Description
        data["description"] = (
            listing.get("description")
            or listing.get("body")
            or listing.get("text")
            or ""
        )

        # Location / address
        location = listing.get("location") or listing.get("address") or {}
        if isinstance(location, dict):
            street = location.get("street") or location.get(
                "streetAddress") or ""
            city = location.get("city") or ""
            data["address"] = ", ".join(
                p for p in [street, city] if p) or street
            data["district"] = (
                location.get("area")
                or location.get("neighborhood")
                or location.get("district")
                or location.get("locality")
                or ""
            )
        elif isinstance(location, str):
            data["address"] = location

        # Coordinates — search the entire __NEXT_DATA__ tree (Qasa nests these variably)
        if not data.get("lat") or not data.get("lng"):
            lat, lng = _find_coords_in_tree(next_data)
            if lat is not None:
                data["lat"] = lat
                data["lng"] = lng

        # Images
        for img_key in ("images", "photos", "pictures", "media"):
            imgs = listing.get(img_key)
            if isinstance(imgs, list) and imgs:
                urls = []
                for img in imgs[:10]:
                    url = (
                        img.get("url") or img.get(
                            "src") or img.get("uri") or ""
                        if isinstance(img, dict)
                        else str(img)
                    )
                    if url:
                        urls.append(_normalize_image_url(url))
                if urls:
                    data["images"] = urls
                break

        # Boolean amenities from listing fields
        amenity_map = {
            "has_washing_machine": ("washingMachine", "washer", "laundry"),
            "has_dryer": ("dryer", "tumbleDryer", "torktumlare"),
            "has_dishwasher": ("dishwasher", "diskmaskin"),
        }
        for field, keys in amenity_map.items():
            for key in keys:
                val = listing.get(key)
                if isinstance(val, bool):
                    data[field] = val
                    break

    except Exception as e:
        logger.debug(f"Error parsing __NEXT_DATA__: {e}")


# ── DOM fallback ──────────────────────────────────────────────────────────────

def _scrape_listing_page_dom(page, data: dict):
    """Fill any missing fields by scraping the DOM and page text."""
    # Try to expand truncated description before grabbing text
    for read_more_sel in ('button:has-text("Read more")', 'button:has-text("Läs mer")'):
        try:
            page.click(read_more_sel, timeout=2000)
            page.wait_for_timeout(500)
            break
        except Exception:
            continue

    try:
        full_text = page.inner_text("body") or ""
    except Exception:
        full_text = ""

    # ── Title ─────────────────────────────────────────────────────────────────
    if not data.get("title"):
        try:
            el = page.query_selector("h1")
            if el:
                data["title"] = el.inner_text().strip()
        except Exception:
            pass

    # Address & district from h1: "Forskningsringen, Sundbyberg" → street, city
    if data.get("title") and not data.get("address"):
        parts = [p.strip() for p in data["title"].split(",")]
        if len(parts) >= 2:
            data["address"] = parts[0]
            data["district"] = parts[-1]
        elif len(parts) == 1:
            data["address"] = parts[0]

    # ── JS global state (Apollo etc.) for price ───────────────────────────────
    if not data.get("price_sek"):
        try:
            js_blob = page.evaluate("""() => {
                const candidates = [
                    window.__APOLLO_STATE__,
                    window.__INITIAL_STATE__,
                    window.__REDUX_STATE__,
                    window.__STATE__,
                ];
                for (const s of candidates) {
                    if (s && typeof s === 'object') return JSON.stringify(s);
                }
                return null;
            }""")
            if js_blob:
                _extract_price_from_json_blob(js_blob, data)
        except Exception:
            pass

    # application/json script tags
    if not data.get("price_sek"):
        try:
            scripts = page.evaluate("""() => {
                const tags = document.querySelectorAll(
                    'script[type="application/json"], script[id*="data"], script[id*="state"]'
                );
                return Array.from(tags)
                    .map(s => s.textContent)
                    .filter(t => t && t.length < 200000);
            }""")
            for blob in (scripts or []):
                if _extract_price_from_json_blob(blob, data):
                    break
        except Exception:
            pass

    # ── Numeric fields from text ──────────────────────────────────────────────
    if not data.get("price_sek") and full_text:
        data["price_sek"] = _parse_price(full_text)
    if not data.get("rooms") and full_text:
        data["rooms"] = _parse_rooms(full_text)
    if not data.get("size_sqm") and full_text:
        data["size_sqm"] = _parse_size(full_text)

    # ── Description ───────────────────────────────────────────────────────────
    if not data.get("description"):
        for sel in (
            "[class*='HomeDescription']",
            "[class*='description']",
            "[data-testid*='description']",
            "main p",
            "article",
        ):
            try:
                el = page.query_selector(sel)
                if el:
                    text = el.inner_text().strip()
                    if len(text) > 50:
                        data["description"] = text
                        break
            except Exception:
                continue

    # ── Images ────────────────────────────────────────────────────────────────
    if not data.get("images"):
        try:
            imgs = page.query_selector_all(
                "img[src*='qasa'], img[src*='cdn'], img[src*='images'], img[src*='storage']"
            )
            urls = []
            for img in imgs[:10]:
                src = img.get_attribute("src") or ""
                if src and not src.endswith(".svg") and "placeholder" not in src.lower():
                    urls.append(_normalize_image_url(src))
            if urls:
                data["images"] = urls
        except Exception:
            pass

    # ── Coordinates from JSON-LD or Leaflet tile URLs (DOM fallback) ──────────
    if not data.get("lat") or not data.get("lng"):
        try:
            # 1. JSON-LD structured data (schema.org/Place or GeoCoordinates)
            ld_texts = page.evaluate("""() =>
                Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                    .map(s => s.textContent)
            """)
            for ld_text in (ld_texts or []):
                try:
                    ld = json.loads(ld_text)
                    lat, lng = _find_coords_in_tree(ld)
                    if lat is not None:
                        data["lat"] = lat
                        data["lng"] = lng
                        break
                except Exception:
                    pass
        except Exception:
            pass

    if not data.get("lat") or not data.get("lng"):
        try:
            # 2. Leaflet map tile URLs encode z/x/y — extract map center via JS
            coords = page.evaluate("""() => {
                // Leaflet exposes map instances on L
                if (window.L && window.L._instances) {
                    const maps = Object.values(window.L._instances);
                    if (maps.length > 0) {
                        const c = maps[0].getCenter();
                        return {lat: c.lat, lng: c.lng};
                    }
                }
                // Also try reading tile img src to decode z/x/y
                const tiles = document.querySelectorAll('img.leaflet-tile[src]');
                for (const t of tiles) {
                    const m = t.src.match(/\\/tile\\.openstreetmap\\.org\\/(\\d+)\\/(\\d+)\\/(\\d+)/);
                    if (m) {
                        const z = parseInt(m[1]), x = parseInt(m[2]), y = parseInt(m[3]);
                        const n = Math.PI - 2 * Math.PI * y / Math.pow(2, z);
                        const lat = 180 / Math.PI * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
                        const lng = x / Math.pow(2, z) * 360 - 180;
                        return {lat, lng};
                    }
                }
                return null;
            }""")
            if coords and coords.get("lat") and coords.get("lng"):
                lat, lng = float(coords["lat"]), float(coords["lng"])
                if 55.0 < lat < 70.0 and 10.0 < lng < 25.0:
                    data["lat"] = lat
                    data["lng"] = lng
        except Exception:
            pass

    # ── Parse rich metadata from full page text ───────────────────────────────
    if full_text:
        _parse_qasa_page_text(full_text, data)


def _parse_qasa_page_text(text: str, data: dict):
    """
    Parse listing metadata from the full visible page text.
    Covers: home type, furnishing, shared/entire, all amenities,
    service fee, electricity, deposit, dates, floor, house rules.

    Key Qasa page-text quirks:
    - Non-breaking spaces (\xa0) appear between "SEK" and the number
    - Double newlines separate label from value: "Rent\n\nSEK\xa013,000"
    - Electricity: "Electricity fee\n\nIncluded" (double newline)
    """
    tl = text.lower()

    # ── Home type ─────────────────────────────────────────────────────────────
    if not data.get("home_type"):
        for label, key in (
            ("terrace house", "terrace_house"),
            ("apartment",     "apartment"),
            ("house",         "house"),
            ("cottage",       "cottage"),
            ("dorm",          "dorm"),
        ):
            if label in tl:
                data["home_type"] = key
                break

    # ── Furnishing ────────────────────────────────────────────────────────────
    if not data.get("furnishing"):
        if "unfurnished" in tl:
            data["furnishing"] = "unfurnished"
        elif "partially furnished" in tl or "partly furnished" in tl:
            data["furnishing"] = "partially_furnished"
        elif "furnished" in tl:
            data["furnishing"] = "furnished"

    # ── Shared vs entire ──────────────────────────────────────────────────────
    if data.get("is_shared") is None:
        if "shared home" in tl:
            data["is_shared"] = True
        elif "entire home" in tl:
            data["is_shared"] = False

    # ── Base rent (not monthly total which includes service fee) ──────────────
    # Page format: "Rent\n\nSEK\xa013,000"  (double newline + non-breaking space)
    if not data.get("price_sek"):
        m = re.search(
            r"(?<!\w)Rent\n\n\s*SEK[\s\xa0]*([\d,\xa0\s]+)", text, re.IGNORECASE)
        if m:
            try:
                val = int(re.sub(r"[,\s\xa0]", "", m.group(1)))
                if 1_000 < val < 200_000:
                    data["price_sek"] = val
            except ValueError:
                pass

    # ── Service fee: "Service fee\n\nSEK\xa0773" ─────────────────────────────
    if not data.get("service_fee_sek"):
        m = re.search(
            r"service fee\s*\n+\s*SEK[\s\xa0]*([\d,\xa0\s]+)", text, re.IGNORECASE)
        if m:
            try:
                val = int(re.sub(r"[,\s\xa0]", "", m.group(1)))
                if 0 < val < 50_000:
                    data["service_fee_sek"] = val
            except ValueError:
                pass

    # ── Electricity: "Electricity fee\n\nIncluded" ────────────────────────────
    # Use re.DOTALL so . matches newlines
    if data.get("electricity_included") is None:
        if re.search(r"electricity fee[\s\S]{0,10}included", text, re.IGNORECASE):
            data["electricity_included"] = True
        elif re.search(r"electricity fee[\s\S]{0,10}not included", text, re.IGNORECASE):
            data["electricity_included"] = False

    # ── Deposit ───────────────────────────────────────────────────────────────
    if not data.get("deposit_months"):
        m = re.search(r"deposit[\s\S]{0,15}(\d+)\s*month", text, re.IGNORECASE)
        if m:
            data["deposit_months"] = int(m.group(1))

    # ── Floor from text: "2nd floor", "floor 3", "våning 3" ──────────────────
    if not data.get("floor"):
        for pattern in (
            r"(\d+)(?:st|nd|rd|th)\s+floor",
            r"\bfloor\s+(\d+)\b",
            r"\bvåning\s+(\d+)\b",
        ):
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                if 0 <= val <= 50:
                    data["floor"] = val
                    break

    # Available from
    if not data.get("available_from"):
        # "Move in\n\nNow", "Available from\n\nNow", bare "Now →", or "Dates\nNow\n..."
        if re.search(
            r"(?:move.?in|available\s+from)[\s\S]{0,20}\bnow\b"
            r"|\bnow\s*[\u2192\u2013\u2014\-]\s*\d{4}-\d{2}-\d{2}"
            r"|dates[\s\S]{0,30}\bnow\b",
            text, re.IGNORECASE
        ):
            data["available_from"] = "now"
        else:
            # Specific date patterns: "2025-04-01", "Apr 1, 2025", "1 Apr 2025"
            for pat in (
                r"dates[\s\S]{0,20}?(\d{4}-\d{2}-\d{2})",
                r"(?:move.?in|available\s+from)[\s\S]{0,30}(\d{4}-\d{2}-\d{2})",
                r"(?:move.?in|available\s+from)[\s\S]{0,30}(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})",
                r"(?:move.?in|available\s+from)[\s\S]{0,30}((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
            ):
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    raw = m.group(1).strip()
                    # Normalise to YYYY-MM-DD if it's already in that format
                    if re.match(r"\d{4}-\d{2}-\d{2}", raw):
                        data["available_from"] = raw
                    else:
                        # Store the human-readable string; the route will parse it
                        data["available_from"] = raw
                    break

    # Available until
    if not data.get("available_until"):
        if "until further notice" in tl:
            data["available_until"] = "until_further_notice"
        else:
            for pat in (
                r"dates[\s\S]{0,50}?[\u2192\u2013\u2014>]\s*(\d{4}-\d{2}-\d{2})",
                r"move[\ \-]*out[\s\S]{0,20}(\d{4}-\d{2}-\d{2})",
                r"end\s+date[\s\S]{0,20}(\d{4}-\d{2}-\d{2})",
                r"until\s+(\d{4}-\d{2}-\d{2})",
                r"[\u2192\u2013\u2014>]\s*(\d{4}-\d{2}-\d{2})",
                r"\bnow\s*\n\s*(\d{4}-\d{2}-\d{2})",
            ):
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    data["available_until"] = m.group(1)
                    break

    # ── Comprehensive amenity detection ──────────────────────────────────────
    detected = []
    for key, keywords in QASA_AMENITIES:
        if any(kw in tl for kw in keywords):
            detected.append(key)
    if detected:
        existing = data.get("amenities") or []
        data["amenities"] = list(dict.fromkeys(existing + detected))
    # Sync legacy boolean fields
    amenities_set = set(data.get("amenities") or [])
    data["has_washing_machine"] = "washing_machine" in amenities_set
    data["has_dryer"] = "tumble_dryer" in amenities_set
    data["has_dishwasher"] = "dishwasher" in amenities_set

    # ── House rules ───────────────────────────────────────────────────────────
    rules = data.get("house_rules") or {}
    if "pets_allowed" not in rules:
        rules["pets_allowed"] = "no pets" not in tl
    if "smoking_allowed" not in rules:
        rules["smoking_allowed"] = "no smoking" not in tl
    if "wheelchair_accessible" not in rules:
        rules["wheelchair_accessible"] = (
            "wheelchair accessible" in tl and "not wheelchair accessible" not in tl
        )
    m = re.search(r"up to (\d+) tenants?", text, re.IGNORECASE)
    if m:
        rules["max_tenants"] = int(m.group(1))
    data["house_rules"] = rules


def _extract_price_from_json_blob(blob: str, data: dict) -> bool:
    """Search a raw JSON string for rent value. Returns True if found."""
    for pattern in (
        r'"rent"\s*:\s*(\d{4,6})',
        r'"price"\s*:\s*(\d{4,6})',
        r'"monthlyRent"\s*:\s*(\d{4,6})',
        r'"rentAmount"\s*:\s*(\d{4,6})',
        r'"pricePerMonth"\s*:\s*(\d{4,6})',
    ):
        m = re.search(pattern, blob)
        if m:
            val = int(m.group(1))
            if 1_000 < val < 200_000:
                data["price_sek"] = val
                return True
    return False


# ── Cookie/banner dismissal ───────────────────────────────────────────────────

def _dismiss_cookie_banner(page):
    for sel in (
        'button[id*="accept"]',
        'button:has-text("Acceptera alla")',
        'button:has-text("Acceptera")',
        'button:has-text("Godkänn")',
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        '[data-testid*="cookie"] button',
    ):
        try:
            page.click(sel, timeout=2000)
            return
        except Exception:
            continue


# ── Shared page data extraction ───────────────────────────────────────────────

def _extract_page_data(page, url: str) -> dict:
    """Run full extraction pipeline on an already-loaded page."""
    data: dict = {"url": url, "source": "qasa"}

    # 1. Try __NEXT_DATA__
    try:
        next_data_text = page.evaluate(
            "() => { const el = document.getElementById('__NEXT_DATA__'); return el ? el.textContent : null; }"
        )
        if next_data_text:
            _extract_from_next_data(json.loads(next_data_text), data)
    except Exception as e:
        logger.debug(f"__NEXT_DATA__ parse failed for {url}: {e}")

    # 2. DOM fallback for anything still missing
    _scrape_listing_page_dom(page, data)

    # 3. Defaults for required DB fields
    if not data.get("title"):
        data["title"] = f"Qasa listing ({url.rstrip('/').split('/')[-1]})"
    if not data.get("price_sek"):
        data["price_sek"] = 0
    if not data.get("rooms"):
        data["rooms"] = 1

    # 4. Amenities from description text (fills any field not already set)
    amenity_text = f"{data.get('title', '')} {data.get('description', '')}"
    for field, val in parse_amenities(amenity_text).items():
        if field not in data:
            data[field] = val

    return data


def _new_browser_context(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
    )
    return browser, context


def _goto(page, url: str):
    """Navigate with graceful timeout fallback."""
    try:
        page.goto(url, wait_until="networkidle", timeout=30_000)
    except Exception:
        page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_timeout(3_000)


# ── Public API ────────────────────────────────────────────────────────────────

def extract_from_url(url: str) -> dict | None:
    """
    Extract a single Qasa listing from its URL using Playwright.

    Returns a dict ready to be saved as a Listing, or None on failure.
    The dict may include partial data — callers should validate required fields.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "Playwright not installed. Run: playwright install chromium")
        return None

    try:
        with sync_playwright() as p:
            browser, context = _new_browser_context(p)
            page = context.new_page()

            try:
                _goto(page, url)
            except Exception as e:
                logger.error(f"Could not load {url}: {e}")
                browser.close()
                return None

            _dismiss_cookie_banner(page)
            data = _extract_page_data(page, url)
            browser.close()
            return data

    except Exception as e:
        logger.error(f"extract_from_url failed for {url}: {e}")
        return None


def _build_search_url(min_price=None, max_price=None, min_rooms=None, max_rooms=None) -> str:
    params = []
    if min_price:
        params.append(f"minRent={min_price}")
    if max_price:
        params.append(f"maxRent={max_price}")
    if min_rooms:
        params.append(f"minRooms={min_rooms}")
    if max_rooms:
        params.append(f"maxRooms={max_rooms}")
    return SEARCH_BASE_URL + ("?" + "&".join(params) if params else "")


def scrape_qasa(
    min_price=None,
    max_price=None,
    min_rooms=None,
    max_rooms=None,
    max_listings=MAX_LISTINGS,
) -> list:
    """
    Bulk-scrape Qasa listings from the search page.

    Returns a list of listing dicts (up to max_listings).
    Respects robots.txt spirit: 2-5 s delay between page loads,
    capped at 50 listings per run.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "Playwright not installed. Run: playwright install chromium")
        return []

    search_url = _build_search_url(min_price, max_price, min_rooms, max_rooms)
    logger.info(f"Starting Qasa bulk scrape: {search_url}")

    listing_urls: list[str] = []
    listings: list[dict] = []

    # Link patterns that point to individual listings
    LINK_PATTERNS = [
        'a[href*="/listing/"]',
        'a[href*="/bostad/"]',
        'a[href*="/home/"]',
        '[data-testid*="listing"] a',
        '[class*="listing-card"] a',
        '[class*="HomeCard"] a',
        '[class*="home-card"] a',
    ]

    def collect_urls(page):
        for pattern in LINK_PATTERNS:
            els = page.query_selector_all(pattern)
            for el in els:
                href = el.get_attribute("href") or ""
                if href and not href.startswith("http"):
                    href = "https://qasa.se" + href
                if href and href not in listing_urls:
                    listing_urls.append(href)
            if listing_urls:
                break

    try:
        with sync_playwright() as p:
            browser, context = _new_browser_context(p)
            page = context.new_page()

            # ── Step 1: collect listing URLs ──────────────────────────────
            try:
                _goto(page, search_url)
            except Exception as e:
                logger.error(f"Could not load Qasa search page: {e}")
                browser.close()
                return []

            _dismiss_cookie_banner(page)
            page.wait_for_timeout(2_000)

            collect_urls(page)

            # Scroll to trigger lazy-loading of more cards
            for _ in range(6):
                if len(listing_urls) >= max_listings:
                    break
                page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
                page.wait_for_timeout(1_500)
                collect_urls(page)

            listing_urls = listing_urls[:max_listings]
            logger.info(f"Found {len(listing_urls)} listing URLs to process")

            if not listing_urls:
                logger.warning(
                    "No listing URLs found. Qasa's DOM may have changed — "
                    "check selector patterns in scrapers/qasa.py."
                )
                browser.close()
                return []

            # ── Step 2: visit each listing page ──────────────────────────
            for i, listing_url in enumerate(listing_urls):
                logger.info(
                    f"Scraping {i + 1}/{len(listing_urls)}: {listing_url}")
                try:
                    _goto(page, listing_url)
                    data = _extract_page_data(page, listing_url)
                    listings.append(data)
                except Exception as e:
                    logger.warning(f"Failed to scrape {listing_url}: {e}")

                if i < len(listing_urls) - 1:
                    _random_delay()

            browser.close()

    except Exception as e:
        logger.error(f"Bulk scrape failed: {e}")

    logger.info(f"Scrape complete: {len(listings)} listings extracted")
    return listings
