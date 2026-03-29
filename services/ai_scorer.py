"""
AI scoring service using Claude API.

Scores listings 0-100 based on listing details, commute, nearby POIs,
and user preferences from UserSettings.

Batch processing: 5 listings at a time with 1s delay between calls.
Fails gracefully — on parse error, stores raw text and sets score=None.
"""
import json
import logging
import time
import threading

import anthropic

from database.db import db
from database.models import Listing, UserSettings

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
BATCH_SIZE = 5
BATCH_DELAY = 1.0  # seconds between API calls


# ── Public API ───────────────────────────────────────────────────────────────

def score_listing_sync(app, listing_id: int) -> dict:
    """Score a single listing synchronously. Returns result dict."""
    with app.app_context():
        return _score_one(listing_id)


def score_all_async(app) -> None:
    """Score all unscored listings in a background thread."""
    t = threading.Thread(target=_run_score_all, args=(app,), daemon=True)
    t.start()


# ── Internal ─────────────────────────────────────────────────────────────────

def _run_score_all(app) -> None:
    with app.app_context():
        try:
            unscored = Listing.query.filter(Listing.ai_score.is_(None)).all()
            ids = [l.id for l in unscored]
            logger.info(f"Starting AI scoring for {len(ids)} listings")
            for i, listing_id in enumerate(ids):
                try:
                    _score_one(listing_id)
                except Exception as e:
                    logger.error(
                        f"Scoring failed for listing {listing_id}: {e}")
                # Delay between calls; also between batches
                if i < len(ids) - 1:
                    time.sleep(BATCH_DELAY)
        except Exception as e:
            logger.error(f"Bulk scoring failed: {e}")


def _score_one(listing_id: int) -> dict:
    """
    Score a single listing. Stores result in DB.
    Returns dict: {success, score, error}.
    """
    from config import ANTHROPIC_API_KEY
    from services.district_advisor import get_district_profile

    if not ANTHROPIC_API_KEY:
        return {"success": False, "error": "ANTHROPIC_API_KEY not set"}

    listing = Listing.query.get(listing_id)
    if not listing:
        return {"success": False, "error": f"Listing {listing_id} not found"}

    settings = UserSettings.query.get(1)
    district_profile = get_district_profile(listing.district or "")

    prompt = _build_prompt(listing, settings, district_profile)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    result = _call_claude(client, prompt)
    if result is None:
        # Retry once
        logger.warning(
            f"First scoring attempt failed for listing {listing_id}, retrying…")
        time.sleep(1)
        result = _call_claude(client, prompt)

    if result is None:
        listing.ai_comment = "Scoring failed — could not parse AI response."
        db.session.commit()
        return {"success": False, "error": "Failed to parse Claude response after retry"}

    if isinstance(result, str):
        # Raw text fallback
        listing.ai_comment = result
        listing.ai_score = None
        db.session.commit()
        return {"success": False, "error": "Stored raw response; JSON parse failed"}

    # Parsed successfully
    listing.ai_score = result.get("score")
    listing.ai_comment = result.get("summary", "") + (
        f"\n\n{result.get('district_comment', '')}" if result.get(
            "district_comment") else ""
    )
    listing.ai_pros = result.get("pros", [])
    listing.ai_cons = result.get("cons", [])
    db.session.commit()

    logger.info(f"Scored listing {listing_id}: {listing.ai_score}/100")
    return {"success": True, "score": listing.ai_score}


def _call_claude(client: anthropic.Anthropic, prompt: str) -> dict | str | None:
    """
    Call Claude and return:
    - dict: parsed JSON result
    - str: raw text if JSON parse failed
    - None: on API/network error
    """
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            timeout=30,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

        # Extract JSON from response (Claude may wrap in markdown code block)
        json_str = _extract_json(raw)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"JSON parse failed. Raw response: {raw[:200]}")
            return raw  # Fallback: store raw text

    except anthropic.APIConnectionError as e:
        logger.error(f"Claude API connection error: {e}")
        return None
    except anthropic.RateLimitError as e:
        logger.error(f"Claude rate limit: {e}")
        return None
    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Claude: {e}")
        return None


def _extract_json(text: str) -> str:
    """Strip markdown code fences if present, return raw JSON string."""
    if "```" in text:
        lines = text.split("\n")
        inside = False
        json_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                json_lines.append(line)
        return "\n".join(json_lines).strip()
    # Try to find first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end + 1]
    return text


def _build_prompt(listing: Listing, settings: UserSettings | None, district_profile: dict | None) -> str:
    """Build the scoring prompt for Claude."""

    # Amenities list
    amenity_labels = {
        "balcony": "Balcony", "rooftop_terrace": "Rooftop terrace",
        "garden": "Garden", "sauna": "Sauna", "pool": "Pool",
        "fridge": "Fridge", "freezer": "Freezer", "microwave": "Microwave",
        "oven": "Oven", "stove": "Stove", "dishwasher": "Dishwasher",
        "washing_machine": "Washing machine", "tumble_dryer": "Tumble dryer",
        "shower": "Shower", "bathtub": "Bathtub", "toilet": "Toilet",
        "elevator": "Elevator", "storage_room": "Storage room",
        "parking": "Parking", "bike_storage": "Bike storage",
        "internet": "Internet included", "television": "TV included",
    }
    amenities_list = []
    if listing.amenities:
        amenities_list = [amenity_labels.get(a, a) for a in listing.amenities]
    else:
        if listing.has_washing_machine:
            amenities_list.append("Washing machine")
        if listing.has_dryer:
            amenities_list.append("Tumble dryer")
        if listing.has_dishwasher:
            amenities_list.append("Dishwasher")

    # POI counts
    pois = listing.nearby_pois or {}
    supermarkets = pois.get("supermarkets", [])
    parks = pois.get("parks", [])
    gyms = pois.get("gyms", [])

    # Commute details
    commute_info = ""
    if listing.commute_minutes is not None:
        details = listing.commute_details or {}
        lines = ", ".join(details.get("lines", [])) or "N/A"
        changes = details.get("changes", "?")
        commute_info = f"{listing.commute_minutes} minutes ({changes} changes, lines: {lines})"
    else:
        commute_info = "Not calculated"

    # Nearby stops
    stops = listing.nearby_stops or []
    stops_text = ""
    if stops:
        stops_text = ", ".join(
            f"{s.get('name', '?')} ({s.get('walk_min', '?')} min walk)" for s in stops[:3]
        )
    else:
        stops_text = "None found"

    # User preferences
    prefs = ""
    if settings:
        must_haves = []
        if settings.must_have_washing_machine:
            must_haves.append("washing machine")
        if settings.must_have_dryer:
            must_haves.append("dryer")
        if settings.must_have_dishwasher:
            must_haves.append("dishwasher")
        prefs = f"""
User preferences:
- Budget: {settings.budget_min:,}–{settings.budget_max:,} SEK/month
- Rooms: {settings.min_rooms}–{settings.max_rooms}
- Max commute: {settings.max_commute_minutes} minutes
- Must-have amenities: {", ".join(must_haves) if must_haves else "None specified"}
- Preferred districts: {", ".join(settings.preferred_districts or []) or "No preference"}"""
    else:
        prefs = "\nUser preferences: not configured"

    # District context
    district_ctx = ""
    if district_profile:
        district_ctx = f"""
District profile — {district_profile['name']}:
- {district_profile['description']}
- Pros: {", ".join(district_profile['pros'])}
- Cons: {", ".join(district_profile['cons'])}
- Avg rent range: {district_profile['avg_price_range']}
- Safety: {district_profile['safety_note']}
- Green score: {district_profile['green_score']}/10"""

    # Price info
    total_price = listing.price_sek
    if listing.service_fee_sek:
        total_price += listing.service_fee_sek

    prompt = f"""You are evaluating a Stockholm rental apartment. Score it 0–100 based on how well it matches the user's needs.

LISTING DETAILS:
- Title: {listing.title}
- Address: {listing.address or "Not specified"}, {listing.district or "Unknown district"}
- Type: {listing.home_type or "apartment"}{" (shared)" if listing.is_shared else ""}
- Furnishing: {listing.furnishing or "Not specified"}
- Price: {listing.price_sek:,} SEK/month{f" + {listing.service_fee_sek:,} SEK fee = {total_price:,} SEK total" if listing.service_fee_sek else ""}
- Rooms: {listing.rooms}
- Size: {f"{listing.size_sqm} m²" if listing.size_sqm else "Not specified"}
- Floor: {listing.floor if listing.floor is not None else "Not specified"}
- Electricity included: {listing.electricity_included if listing.electricity_included is not None else "Unknown"}
- Amenities: {", ".join(amenities_list) if amenities_list else "None listed"}
- Available from: {listing.available_from if listing.available_from else "Not specified"}

COMMUTE & TRANSIT:
- Commute to work: {commute_info}
- Nearest SL stops: {stops_text}

NEARBY AMENITIES (within 1 km):
- Supermarkets: {len(supermarkets)} ({supermarkets[0]["name"] if supermarkets else "none nearby"})
- Parks/green areas: {len(parks)}
- Gyms: {len(gyms)}
{prefs}
{district_ctx}

DESCRIPTION EXCERPT:
{(listing.description or "")[:500]}

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "score": <integer 0-100>,
  "summary": "<1-2 sentence overall assessment>",
  "pros": ["<pro 1>", "<pro 2>", "<pro 3>"],
  "cons": ["<con 1>", "<con 2>"],
  "district_comment": "<1 sentence about how the district fits the user>",
  "recommendation": "<Worth visiting|Maybe|Skip>"
}}

Scoring guidelines:
- 70–100: Excellent match — meets budget, commute, amenities, good district
- 40–69: Decent — some compromises but overall viable
- 0–39: Poor match — significant issues with budget, commute, or requirements"""

    return prompt
