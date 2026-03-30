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
    ("washing_machine",   ["washing machine", "washing_machine",
     "tvättmaskin", "tvättmöjlighet", "washingmachine"]),
    ("tumble_dryer",      ["tumble dryer",
     "tumble_dryer", "torktumlare", "torkskåp"]),
    ("shower",            ["shower", "dusch"]),
    ("bathtub",           ["bathtub", "bath tub", "badkar"]),
    ("toilet",            ["toilet", "toalett"]),
    ("elevator",          ["elevator", "hiss"]),
    ("storage_room",      ["storage room", "förråd"]),
    ("parking",           ["parking available", "parking", "parkering"]),
    ("bike_storage",      ["bike storage", "cykelrum", "cykelförråd"]),
    ("internet",          ["internet"]),
    ("television",        ["television", "tv"]),
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

        # Description — try multiple key names
        _desc = None
        for _k in ("description", "body", "text", "homeDescription",
                   "listingDescription", "about", "aboutHome",
                   "descriptionHtml", "descriptionText", "content",
                   "bodyText", "rentalDescription", "summary"):
            _v = listing.get(_k)
            if isinstance(_v, str) and len(_v) > 20:
                _desc = _v
                break
        # Also check one level of common nested keys
        if not _desc:
            for _nk in ("rentalProperty", "property", "apartment", "home",
                        "listing", "details", "info"):
                _nested = listing.get(_nk)
                if isinstance(_nested, dict):
                    for _k in ("description", "body", "text", "about",
                               "homeDescription", "content"):
                        _v = _nested.get(_k)
                        if isinstance(_v, str) and len(_v) > 20:
                            _desc = _v
                            break
                if _desc:
                    break
        data["description"] = _desc or ""

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
    # Try to expand truncated description — clicking "Read more" opens a modal on Qasa
    _read_more_clicked = False
    for read_more_sel in ('button:has-text("Read more")', 'button:has-text("Läs mer")',
                          'button:has-text("Visa mer")'):
        try:
            page.click(read_more_sel, timeout=2000)
            page.wait_for_timeout(1500)  # wait for modal to fully render
            _read_more_clicked = True
            break
        except Exception:
            continue

    # Click "Show more" for amenities to reveal all amenities
    try:
        show_more_clicked = False

        # First, close any open modals that might block clicks
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Look for the amenities Show more button specifically
        # It should be near the amenities section
        for show_more_sel in (
            'button:has-text("Show more")',  # Basic
            'button:has-text("Visa mer")',   # Swedish
            'button:has-text("Show all amenities")',  # Explicit
            '[data-testid*="show-more"]',     # Test ID
            'button:has-text("Show more amenities")',  # More specific
            'button[class*="show"]',         # Class-based
            'button[class*="more"]',          # Class-based
            '[aria-label*="more"]',           # ARIA label
        ):
            try:
                # Find all matching buttons
                buttons = page.query_selector_all(show_more_sel)

                for button in buttons:
                    try:
                        # Check if this button is near amenities
                        parent = button.evaluate(
                            'el => el.parentElement?.textContent?.toLowerCase()')
                        if parent and any(word in parent for word in ['amenities', 'balcony', 'dish', 'fridge', 'premium']):
                            # This looks like the amenities button
                            button.click(timeout=2000)
                            page.wait_for_timeout(1500)  # Wait for animation
                            show_more_clicked = True
                            logger.info(
                                f"Clicked amenities show more button with selector: {show_more_sel}")
                            break
                    except Exception as e:
                        logger.debug(
                            f"Failed to click button with selector {show_more_sel}: {e}")
                        continue

                if show_more_clicked:
                    break

            except Exception:
                continue

        if not show_more_clicked:
            # Fallback: try the first Show more button
            try:
                first_button = page.query_selector(
                    'button:has-text("Show more")')
                if first_button:
                    first_button.click(timeout=2000)
                    page.wait_for_timeout(1500)
                    show_more_clicked = True
                    logger.info("Clicked first Show more button as fallback")
            except Exception:
                pass

        if not show_more_clicked:
            logger.info("No show more button found or clicked")
    except Exception as e:
        logger.warning(f"Error clicking show more button: {e}")

    # If modal opened, try to grab description from it before anything else
    if _read_more_clicked and not data.get("description"):
        for modal_sel in ('[role="dialog"]', 'dialog',
                          '[class*="Modal"]', '[class*="modal"]',
                          '[class*="Dialog"]', '[class*="dialog"]',
                          '[class*="Overlay"]', '[class*="overlay"]',
                          '[class*="Sheet"]', '[class*="sheet"]'):
            try:
                el = page.query_selector(modal_sel)
                if el:
                    raw = el.inner_text().strip()
                    _skip = {"about the home", "om bostaden", "close",
                             "stäng", "read more", "läs mer", "visa mer"}
                    lines = [ln.strip() for ln in raw.split("\n")
                             if ln.strip() and ln.strip().lower() not in _skip]
                    desc = "\n\n".join(lines).strip()
                    if len(desc) > 50:
                        data["description"] = desc
                        break
            except Exception:
                continue
        # Close the modal so it doesn't pollute other selectors
        if data.get("description"):
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            except Exception:
                pass

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

    if not data.get("description"):
        for sel in (
            "[class*='HomeDescription']",
            "[class*='description']",
            "[data-testid*='description']",
            "[class*='aboutHome']",
            "[class*='AboutHome']",
            "[class*='listingDescription']",
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

    # Last resort: collect all visible <p> elements from main/article
    if not data.get("description"):
        try:
            els = page.query_selector_all("main p, article p")
            chunks = []
            for el in els:
                t = el.inner_text().strip()
                if len(t) > 40:
                    chunks.append(t)
                if len(chunks) >= 15:
                    break
            if chunks:
                data["description"] = "\n\n".join(chunks)
        except Exception:
            pass

    # ── Amenities from DOM elements (checkboxes, icons, etc.) ─────────────────────
    # Try to get amenities from DOM elements first (more reliable than text)
    detected = []
    try:
        # Look for checked checkboxes or selected amenity elements
        amenity_elements = page.query_selector_all(
            'input[type="checkbox"][checked], [aria-checked="true"], '
            '.amenity.selected, .amenity.active, [class*="amenity"][class*="selected"], '
            '[class*="amenity"][class*="active"], input[type="checkbox"]:checked'
        )

        # If no checked checkboxes found, try to get all checkboxes and check their state
        if not amenity_elements:
            all_checkboxes = page.query_selector_all('input[type="checkbox"]')
            for checkbox in all_checkboxes:
                try:
                    # Check if the checkbox is checked via JavaScript
                    is_checked = checkbox.evaluate('el => el.checked')
                    if is_checked:
                        amenity_elements.append(checkbox)
                        logger.info(
                            "Found checked checkbox via JavaScript evaluation")
                except Exception:
                    continue

        # Also try to find amenity labels with checked indicators
        if not amenity_elements:
            labeled_elements = page.query_selector_all(
                'label:has(input[type="checkbox"][checked]), '
                'label:has([aria-checked="true"]), '
                '[class*="amenity"] label, [class*="feature"] label'
            )
            amenity_elements.extend(labeled_elements)

        dom_amenities = []
        for el in amenity_elements:
            try:
                # Get text from the element or its parent/label
                text = el.inner_text().strip().lower()
                if not text:
                    # Try to get from label or parent
                    label = el.query_selector(
                        'label, .label, [class*="label"]')
                    if label:
                        text = label.inner_text().strip().lower()
                    else:
                        parent = el.evaluate(
                            'el => el.parentElement?.textContent?.toLowerCase()')
                        if parent:
                            text = parent.strip()

                if text and len(text) > 2:
                    dom_amenities.append(text)
                    logger.info(f"Found DOM amenity: {text}")
            except Exception:
                continue

        # Map DOM amenity text to our amenity keys
        for amenity_text in dom_amenities:
            for key, keywords in QASA_AMENITIES:
                if any(kw in amenity_text for kw in keywords):
                    if key not in detected:
                        detected.append(key)
                        logger.info(
                            f"Mapped DOM amenity '{amenity_text}' to key '{key}'")

    except Exception as e:
        logger.warning(f"Error extracting DOM amenities: {e}")

    # Store detected amenities for later processing
    data["_detected_amenities"] = detected

    # ── Images ────────────────────────────────────────────────────────────────
    if not data.get("images"):
        urls = []

        # First try to get images from main gallery
        try:
            imgs = page.query_selector_all(
                "img[src*='qasa'], img[src*='cdn'], img[src*='images'], img[src*='storage']"
            )
            for img in imgs[:20]:  # Increased limit
                src = img.get_attribute("src") or ""
                if src and not src.endswith(".svg") and "placeholder" not in src.lower():
                    urls.append(_normalize_image_url(src))
        except Exception:
            pass

        # Then check for "A second look" section or similar
        try:
            second_look_sections = page.query_selector_all(
                '[class*="second"], [class*="Second"], section:has-text("second"), '
                'div:has-text("A second look"), div:has-text("More photos")'
            )
            for section in second_look_sections:
                try:
                    section_imgs = section.query_selector_all("img")
                    for img in section_imgs:
                        src = img.get_attribute("src") or ""
                        if src and not src.endswith(".svg") and "placeholder" not in src.lower():
                            urls.append(_normalize_image_url(src))
                except Exception:
                    continue
        except Exception:
            pass

        # Also try to find any image containers that might be missed
        try:
            additional_imgs = page.query_selector_all(
                '[data-testid*="image"], [data-testid*="photo"], [data-testid*="gallery"] img'
            )
            for img in additional_imgs:
                src = img.get_attribute("src") or ""
                if src and not src.endswith(".svg") and "placeholder" not in src.lower():
                    urls.append(_normalize_image_url(src))
        except Exception:
            pass

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        if unique_urls:
            data["images"] = unique_urls[:15]  # Limit to 15 best images

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

    # ── Contract type detection ───────────────────────────────────────────────────────
    if not data.get("contract_type"):
        if "first hand contract" in tl or "first-hand contract" in tl:
            data["contract_type"] = "first_hand"
            # First hand contracts should not have service fees
            data["service_fee_sek"] = None
            logger.info("Detected first hand contract")
        elif "second hand contract" in tl or "second-hand contract" in tl:
            data["contract_type"] = "second_hand"
            logger.info("Detected second hand contract")
        elif "sublet" in tl or "subletting" in tl:
            data["contract_type"] = "sublet"
            logger.info("Detected sublet")
        else:
            logger.info("No contract type detected in page text")
    else:
        logger.info(f"Contract type already set: {data.get('contract_type')}")

    # ── Base rent (not monthly total which includes service fee) ──────────────
    # Page format: "Rent\n\nSEK\xa013,000" or "Monthly cost\n\nSEK\xa08,493"  (double newline + non-breaking space)
    if not data.get("price_sek"):
        # Try both "Rent" and "Monthly cost" patterns
        for label in ("Rent", "Monthly cost"):
            # Pattern with double newline (original format)
            m = re.search(
                rf"(?<!\w){label}\n\n\s*SEK[\s\xa0]*([\d,\xa0\s]+)", text, re.IGNORECASE)
            if not m:
                # Pattern with single newline (alternative format)
                m = re.search(
                    rf"(?<!\w){label}\n\s*SEK[\s\xa0]*([\d,\xa0\s]+)", text, re.IGNORECASE)
            if m:
                try:
                    val = int(re.sub(r"[,\s\xa0]", "", m.group(1)))
                    if 1_000 < val < 200_000:
                        data["price_sek"] = val
                        break
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

    # ── Amenities from page text (fallback) ───────────────────────────────────
    # Start with any DOM-detected amenities
    detected = data.get("_detected_amenities", [])

    # Only add text-based amenities if we didn't find any from DOM
    if not detected:
        for key, keywords in QASA_AMENITIES:
            if any(kw in tl for kw in keywords):
                detected.append(key)
                logger.info(f"Found text amenity: {key}")

    if detected:
        existing = data.get("amenities") or []
        data["amenities"] = list(dict.fromkeys(existing + detected))
        logger.info(f"Final detected amenities: {detected}")
    else:
        logger.info("No amenities detected from DOM or page text")

    # Clean up temporary field
    if "_detected_amenities" in data:
        del data["_detected_amenities"]

    # Sync legacy boolean fields
    amenities_set = set(data.get("amenities") or [])
    data["has_washing_machine"] = "washing_machine" in amenities_set
    data["has_dryer"] = "tumble_dryer" in amenities_set
    data["has_dishwasher"] = "dishwasher" in amenities_set

    logger.info(f"Final amenities list: {data.get('amenities')}")
    logger.info(f"Final amenities count: {len(data.get('amenities', []))}")

    # ── House rules ─────────────────────────────────────────────────────────────
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

    # Check if listing is unavailable first
    try:
        page_text = page.inner_text("body") or ""
        if "This listing has been archived" in page_text:
            logger.info(f"Skipping archived listing: {url}")
            return None
        elif "This home has been rented out" in page_text:
            logger.info(f"Skipping rented out listing: {url}")
            return None
    except Exception:
        pass

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

            # Return None for archived listings
            if data is None:
                return None

            return data

    except Exception as e:
        logger.error(f"extract_from_url failed for {url}: {e}")
        return None
