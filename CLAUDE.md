# Stockholm Apartment Finder — CLAUDE.md

## Project Overview
A Flask-based web application to find and evaluate rental apartments in Stockholm.
Scrapes listings from Qasa.com (and supports manual entry), analyzes each listing
using location data (Trafiklab SL + Nominatim), scores them with Claude AI, and presents
results in a split-view UI with Leaflet.js map visualization.

All user preferences (budget, rooms, amenities, work address) are stored in the DB via the Settings UI — never hardcoded.

---

## Tech Stack
- **Backend:** Python 3.11+, Flask, SQLAlchemy
- **Database:** SQLite (`./database/apartment_finder.db`)
- **Frontend:** HTML + Tailwind CSS (CDN) + Vanilla JS + Leaflet.js (CDN)
- **APIs:** Trafiklab (SL), Anthropic Claude, OpenStreetMap Nominatim (free geocoding), Overpass API (free POIs)
- **Optional:** Google Maps (Geocoding + Directions) — better accuracy than Nominatim
- **Scraping:** Playwright (Qasa is JS-rendered)

---

## Project Structure
```
├── app.py                  # Flask entry point
├── config.py               # API keys, app config (loaded from .env)
├── seed_data.py            # Seed fake listings for UI dev (source="seed")
├── database/
│   ├── models.py           # SQLAlchemy models
│   └── db.py               # DB init and session
├── scrapers/
│   └── qasa.py             # Qasa.com: bulk scraper + single URL extractor
├── services/
│   ├── maps.py             # Geocoding: Nominatim (free) or Google Maps (optional)
│   ├── transit.py          # Trafiklab SL API calls
│   ├── overpass.py         # OpenStreetMap Overpass: nearby POIs (free, no key)
│   ├── ai_scorer.py        # Claude API scoring + comments
│   └── district_advisor.py # Stockholm district info + recommendations (static JSON)
├── routes/
│   ├── listings.py         # Listing CRUD + scrape trigger + manual add + URL extract
│   ├── api.py              # JSON endpoints: map data, POIs, transit routes
│   └── settings.py         # User preferences API
├── templates/
│   ├── base.html
│   ├── index.html          # Main split view: listings left + map right
│   ├── add_listing.html    # Manual listing entry / URL paste form
│   ├── settings.html       # Preferences panel
│   └── districts.html      # District guide page
└── static/
    ├── css/style.css       # Dark/light mode variables + custom styles
    └── js/
        ├── app.js          # Main app: split view, expandable cards, map interaction
        ├── filters.js
        └── theme.js        # Dark/light mode toggle
```

---

## Database Models

### UserSettings
- work_address, work_lat, work_lng
- budget_min, budget_max (int, SEK/month)
- min_rooms, max_rooms (int)
- floor_min (int, nullable)
- must_have_washing_machine, must_have_dryer, must_have_dishwasher (bool)
- preferred_districts (JSON list)
- max_commute_minutes (int)
- theme ("light" or "dark", default "light")

### Listing
- id, source ("qasa" / "manual" / "seed")
- url (UNIQUE constraint — DB-level deduplication)
- title, description (text)
- address, district, lat, lng
- price_sek, rooms, floor (nullable), size_sqm (nullable)
- has_washing_machine, has_dryer, has_dishwasher (bool)
- available_from (date, nullable)
- images (JSON list of URLs)
- commute_minutes (nullable), commute_details (JSON), nearby_stops (JSON)
- nearby_pois (JSON — cached Overpass results: supermarkets, parks, gyms within 1km)
- ai_score (int 0-100, nullable), ai_comment (text), ai_pros, ai_cons (JSON lists)
- is_saved (bool), application_status ("not_applied"/"applied"/"waiting"/"rejected"/"accepted")
- application_date (date, nullable), notes (text)
- created_at, updated_at

---

## Environment Variables (.env)

```
TRAFIKLAB_RESROBOT_KEY=    # ResRobot v2.1 — journey planning
TRAFIKLAB_STOPS_KEY=       # Stops data API — nearby stops (50 req/30d on Bronze — cache aggressively)
ANTHROPIC_API_KEY=
FLASK_SECRET_KEY=
GOOGLE_MAPS_API_KEY=       # Optional — leave blank to use Nominatim (free)
```

---

## Key Conventions

- **Settings:** Always load from DB (`UserSettings`), never hardcode preferences
- **Secrets:** All API keys via .env, never commit .env
- **Scraping:** Randomized 2-5s delays, respect Retry-After, cap 50 listings/run
- **Geocoding:** `if GOOGLE_MAPS_API_KEY: use_google() else: use_nominatim()` (1 req/s, User-Agent required)
- **Deduplication:** Handle `IntegrityError` on Listing.url gracefully
- **AI scoring:** `json.loads` in try/except; retry once on failure; batch 5 at a time; `ai_score=None` on persistent failure
- **API calls:** try/except with timeouts (10s geocoding, 30s AI); never crash the app
- **Zero-key mode:** App must fully run with no API keys — manual entry, seed data, and basic UI always work
- **Error UX:** User-friendly messages only, no raw tracebacks; missing API keys → dismissible banner
- **Simplicity:** Prefer simple over clever; don't add features beyond what's asked
