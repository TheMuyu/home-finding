# Stockholm Apartment Finder — CLAUDE.md

## Project Overview
A Flask-based web application to help find and evaluate rental apartments in Stockholm.
The app scrapes listings from Qasa.se (and supports manual entry), analyzes each listing
using location data (Google Maps + Trafiklab SL), scores them with Claude AI, and presents
results in a clean interactive UI with map visualization.

Everything configurable (budget, rooms, amenities, work address) is managed via the UI.
No hardcoded user preferences.

---

## Tech Stack
- **Backend:** Python 3.11+, Flask
- **Database:** SQLite (local, via SQLAlchemy) — simple, no setup needed
- **Frontend:** HTML + Tailwind CSS + Vanilla JS + Leaflet.js (maps)
- **APIs:** Trafiklab (SL) API, Anthropic Claude API, OpenStreetMap Nominatim (free geocoding), Overpass API (free nearby POIs)
- **Optional API:** Google Maps (Geocoding + Directions) — upgrade for better accuracy
- **Scraping:** Playwright (Qasa is JS-rendered)

---

## Project Structure
```
stockholm-finder/
├── app.py                  # Flask entry point
├── config.py               # API keys, app config (loaded from .env)
├── seed_data.py            # Seed 8-10 fake listings for UI development
├── .env                    # Secret keys (never commit)
├── .env.example            # Template for .env
├── requirements.txt
├── database/
│   ├── models.py           # SQLAlchemy models
│   └── db.py               # DB init and session
├── scrapers/
│   └── qasa.py             # Qasa.se: bulk scraper + single URL extractor
├── services/
│   ├── maps.py             # Geocoding: Nominatim (free) or Google Maps (optional)
│   ├── transit.py          # Trafiklab SL API calls
│   ├── overpass.py         # OpenStreetMap Overpass: nearby POIs (free, no key)
│   ├── ai_scorer.py        # Claude API scoring + comments
│   └── district_advisor.py # Stockholm district info + recommendations
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
    ├── css/
    │   └── style.css       # Dark/light mode variables + custom styles
    └── js/
        ├── app.js          # Main app: split view, expandable cards, map interaction
        ├── filters.js
        └── theme.js        # Dark/light mode toggle
```

---

## Database Models (SQLite)

### UserSettings
- work_address (string)
- work_lat, work_lng (float)
- budget_min, budget_max (int, SEK/month)
- min_rooms, max_rooms (int)
- floor_min (int, optional)
- must_have_washing_machine (bool)
- must_have_dryer (bool)
- must_have_dishwasher (bool)
- preferred_districts (JSON list)
- max_commute_minutes (int)
- theme (string, "light" or "dark", default "light")

### Listing
- id
- source (string: "qasa" or "manual")
- url (string, UNIQUE constraint — enforced at DB level for deduplication)
- title, description (text)
- address, district (string)
- lat, lng (float)
- price_sek (int)
- rooms (int)
- floor (int, nullable)
- has_washing_machine (bool)
- has_dryer (bool)
- has_dishwasher (bool)
- size_sqm (int, nullable)
- available_from (date, nullable)
- images (JSON list of URLs)
- commute_minutes (int, nullable)
- commute_details (JSON — transit steps)
- nearby_stops (JSON)
- nearby_pois (JSON — cached Overpass results: supermarkets, parks, gyms within 1km)
- ai_score (int 0-100, nullable)
- ai_comment (text, nullable)
- ai_pros (JSON list)
- ai_cons (JSON list)
- is_saved (bool, default False)
- application_status (string, nullable: "not_applied" / "applied" / "waiting" / "rejected" / "accepted")
- application_date (date, nullable)
- notes (text — user's own notes)
- created_at, updated_at

> Note: Nearby POIs (supermarkets, parks, gyms) fetched from OpenStreetMap Overpass API — completely
> free, no API key needed. Results cached in `nearby_pois` JSON field per listing.
> Geocoding uses free Nominatim by default; set GOOGLE_MAPS_API_KEY in .env for better accuracy.

---

## API Keys Needed (add to .env)

Trafiklab uses **two separate API keys** — one per API product:

```
# Trafiklab — two separate keys (free at trafiklab.se)
TRAFIKLAB_RESROBOT_KEY=    # ResRobot v2.1 — journey planning (25 000 req/30d on Bronze)
TRAFIKLAB_STOPS_KEY=       # Stops data API — nearby stops lookup (50 req/30d on Bronze)

ANTHROPIC_API_KEY=
FLASK_SECRET_KEY=

# Optional — leave blank to use free alternatives
GOOGLE_MAPS_API_KEY=       # Better geocoding accuracy. If blank → uses Nominatim (free)
```

---

## Stockholm District Guide (Built-in Data)
Include as static JSON in district_advisor.py.
Each entry: name, description, pros, cons, avg_price_range, sl_lines, green_score, safety_note.

**Recommended:**
- Hägersten — calm, green, good transport
- Älvsjö — quiet, nature, families
- Enskede — safe, parks, classic Stockholm feel
- Midsommarkransen — trendy but calm, good SL access
- Fruängen — affordable, peaceful, metro access
- Bandhagen — similar to Högdalen (already familiar)
- Stureby — quiet residential, green
- Björkhagen — nature, lakes, very calm

**Flagging:**
- Flag districts with known higher crime index using public data
- Let Claude AI comment on district fit based on user preferences
- Don't hard-exclude any district — just flag and explain in UI

---

## Seed Data

`seed_data.py` — run with `python seed_data.py` to populate 8-10 fake listings across
different districts, price ranges, and amenity combinations. This allows building and
testing the UI without needing working scrapers or API keys.

Each seed listing should have realistic Stockholm addresses, varied prices (8000-18000 SEK),
1-3 rooms, and randomized amenities. Set `source="seed"` so they can be easily cleared.
Include a `clear_seed_data()` function.

---

## Error Handling Strategy

### Missing API Keys
- On startup, check which API keys are set in .env
- Show a dismissible banner on every page listing missing keys and what features are disabled
- App must still run with zero API keys (manual entry + seed data + basic UI all work)

### Scraper Failures
- Wrap all scraping in try/except, log errors, return partial results
- Show toast notification: "Scraped X listings, Y errors"
- Never crash the app on scrape failure

### AI Scoring Failures
- Parse Claude response with `json.loads` inside try/except
- On malformed JSON: retry once, then store raw response in `ai_comment` and set `ai_score = None`
- Batch scoring: process 5 listings at a time, not all at once
- Show per-listing error state ("Scoring failed — retry?")

### General
- All API calls wrapped in try/except with timeouts (10s for geocoding, 30s for AI)
- User-friendly error messages, never raw tracebacks in UI
- Empty states with helpful messages (no listings yet, no scores yet, etc.)

---

## Session Plan

---

### SESSION 1 — Project Setup, Database & Settings
**Goal:** Scaffold the project, set up Flask, SQLite, seed data, and settings UI.

**Tasks:**
1. Create folder structure as above
2. Set up Flask app with Blueprint routing
3. Install dependencies → requirements.txt
4. Create SQLAlchemy models (UserSettings + Listing)
   - UNIQUE constraint on Listing.url
   - All JSON fields default to empty list/dict
5. Create `.env.example` with all 4 keys
6. Create `seed_data.py` with 8-10 fake Stockholm listings
7. Build **Settings Page UI:**
   - Work address input (text → geocode on save via Google Maps, or just store text if no API key)
   - Budget range (min/max SEK sliders)
   - Room count (min/max)
   - Max commute time (slider, minutes)
   - Amenity toggles: washing machine / dryer / dishwasher
   - Preferred districts (multi-select from recommended list)
   - Theme toggle (dark/light)
   - Save button → stores to SQLite UserSettings table
8. Basic navbar with: Listings (split view with map) | Districts | Settings | + Add Listing
9. API key health check banner (missing keys warning)

**Deliverable:** Running Flask app, settings page saves/loads, seed data populates listings.

---

### SESSION 2 — Qasa Scraper + Manual Entry
**Goal:** Scrape listings from Qasa.se and provide manual entry fallback.

**Tasks:**
1. **Qasa.se scraper (qasa.py):**
   - Use Playwright for JS rendering
   - Search URL builder with filters (price, rooms, Stockholm area)
   - Parse: title, price, rooms, address, description, images, URL
   - Handle pagination (cap at 50 listings per run)
   - Randomized delays: 2-5 seconds between page loads
   - Deduplication by URL (UNIQUE constraint handles DB level)

2. **Scraper runner:**
   - Flask route: POST /scrape → runs Qasa scraper
   - Return count of new vs duplicate listings
   - UI button: "Refresh Listings" with loading spinner
   - Toast notification: "Found X new listings"

3. **Add Listing page (add_listing.html) — two modes:**

   **Mode A: Paste Qasa URL (primary flow)**
   - Single input field at top: "Paste a Qasa listing URL"
   - On submit → backend visits URL with Playwright, extracts all fields:
     title, price, rooms, address, district, floor, size, description, images, amenities
   - Shows pre-filled preview form with all extracted data
   - User reviews, edits anything if needed, then clicks "Save Listing"
   - Reuses the same Playwright + parsing logic from qasa.py scraper
   - Stores with source="qasa"
   - If extraction fails: show error toast + offer to switch to manual mode
     with the URL pre-filled

   **Mode B: Full manual entry (fallback)**
   - Toggle or tab: "Enter manually instead"
   - Full form: URL (optional), title, address, price, rooms, floor, size,
     description, amenity checkboxes, available from date
   - Stores with source="manual"

   - "Add Listing" button accessible from navbar and listings page
   - After save → redirect to listing detail page

4. Parse amenities from description text (used by both scraper and URL extract):
   - Keyword matching: "tvättmaskin", "diskmaskin", "torktumlare", "tvättmöjlighet"
   - Also match English: "washing machine", "dishwasher", "dryer"
   - Set boolean fields accordingly
   - On manual entry: user sets amenities via checkboxes directly

**Deliverable:** Listings stored in DB via bulk scraping, single URL paste, or manual entry.

---

### SESSION 3 — Geocoding & Trafiklab Integration
**Goal:** For each listing, get coordinates, calculate commute time, and find nearby transit.

**Tasks:**
1. **maps.py — Geocoding service (free by default, Google optional):**
   - **Default: OpenStreetMap Nominatim (no API key needed)**
     - Geocode listing address → lat/lng
     - Geocode work address (from settings) → lat/lng
     - Rate limit: max 1 request/second (Nominatim policy)
     - User-Agent header required (set to app name)
     - Cache geocoded results — don't re-geocode already resolved addresses
   - **If GOOGLE_MAPS_API_KEY is set: use Google Geocoding API instead**
     - Better accuracy for Swedish addresses
     - Also enables Google Directions API for transit commute as a backup
   - Logic: `if google_key: use_google() else: use_nominatim()`

2. **transit.py — Trafiklab SL service (primary commute calculator):**
   - Two separate API keys (see API Keys section):
     - `TRAFIKLAB_RESROBOT_KEY` → ResRobot v2.1 for journey planning (listing → work address)
     - `TRAFIKLAB_STOPS_KEY` → Stops data API for nearest stops lookup
   - ResRobot: extract total minutes, number of changes, transit lines used, route geometry
   - Stops data: find closest stops + walk time. **Cache aggressively** — only 50 req/30d on Bronze.
   - Store in listing.commute_minutes + listing.commute_details + listing.nearby_stops
   - This is the primary commute source regardless of Google key presence

3. **overpass.py — OpenStreetMap Overpass API (free, no key needed):**
   - Query nearby POIs within 1km of listing lat/lng
   - Categories:
     - Supermarkets/grocery: `shop=supermarket`, `shop=convenience`
     - Parks & green areas: `leisure=park`, `leisure=garden`, `leisure=nature_reserve`
     - Gyms: `leisure=fitness_centre`, `leisure=sports_centre`
   - Return: name, type, lat/lng, distance from listing
   - Cache results in listing.nearby_pois (JSON)
   - Rate limit: be polite, 1 request/second, no key needed
   - Overpass endpoint: `https://overpass-api.de/api/interpreter`

4. **Enrichment runner:**
   - After scraping or adding a listing, auto-enrich if missing lat/lng, commute, or POI data
   - Skip already-enriched listings
   - Simple threading (no Celery)
   - Show commute time badge on listing cards
   - Graceful fallback: if APIs unavailable, listing still shows without enrichment data

**Deliverable:** Each listing shows commute time, nearby SL stops, and nearby POIs (supermarkets, parks, gyms).

---

### SESSION 4 — AI Scoring with Claude API
**Goal:** Use Claude API to score and comment on each listing.

**Tasks:**
1. **ai_scorer.py:**
   - Build prompt using:
     - Listing details (price, rooms, floor, amenities, district, size)
     - Commute time + transit details
     - Nearby SL stops
     - Nearby POIs (supermarkets, parks, gyms count + distance)
     - User preferences from UserSettings
     - District character profile from district_advisor.py
   - Ask Claude to return JSON:
     ```json
     {
       "score": 78,
       "summary": "Great commute, quiet district, missing dryer",
       "pros": ["15 min commute", "park nearby", "dishwasher included"],
       "cons": ["No dryer", "Top floor no elevator"],
       "district_comment": "Midsommarkransen is calm and safe, good fit",
       "recommendation": "Worth visiting"
     }
     ```
   - Use claude-sonnet-4-20250514 model
   - Parse response with json.loads in try/except
   - On failure: retry once, then store raw text in ai_comment, set ai_score = None
   - Batch processing: 5 listings at a time with 1s delay between calls
   - Store results in listing DB fields

2. **UI trigger:**
   - "Score with AI" button per listing
   - "Score All Unscored" bulk button (with progress indicator)
   - Show score as colored badge (green ≥70, yellow 40-69, red <40)
   - Show pros/cons as green/red chips
   - Show AI comment in listing detail view
   - Error state per listing if scoring failed

**Deliverable:** Each listing gets an AI score, pros/cons, and comment.

---

### SESSION 5 — Split View UI (Listings + Map)
**Goal:** Build the main interface: listings on the left, interactive map on the right, expandable detail cards.

**Tasks:**
1. **Split view layout (index.html):**
   - Left panel (scrollable, ~45% width): listing cards + filters
   - Right panel (fixed, ~55% width): Leaflet.js map
   - Responsive: on mobile, stack vertically (listings top, map bottom or toggle)

2. **Listing cards (left panel):**
   - Compact card for each listing:
     - Photo thumbnail (or placeholder)
     - Price, rooms, size, district
     - AI score badge (colored: green ≥70, yellow 40-69, red <40)
     - Commute time badge
     - Amenity icons (washer/dryer/dishwasher)
     - Save ★ toggle
   - Hover on card → highlight corresponding marker on map
   - Click card → expands inline (pushes other cards down)

3. **Expandable card detail (replaces separate detail page):**
   - Expands below the clicked card, within the list
   - Shows:
     - Full image gallery (simple prev/next)
     - Full description text
     - AI score section: score, summary, pros (green), cons (red), recommendation
     - Commute breakdown (minutes, changes, lines)
     - Nearest SL stops with walk time
     - District info snippet (from district_advisor.py)
     - Application status dropdown + date
     - User notes textarea (auto-save on blur)
     - Link to original listing URL
   - "Collapse" button or click card header again to close
   - Only one card expanded at a time (expanding another collapses the current)

4. **Map (right panel):**
   - Leaflet.js with all listing markers
   - Markers color-coded by AI score (green/yellow/red dots)
   - Work address marker (star/flag icon)
   - Click marker → scrolls to that listing card on the left + expands it
   - Marker clustering if many listings overlap in same area

5. **Map interaction on listing select (when a card is expanded):**
   - Map zooms to selected listing area
   - Shows transit route line from listing to work address (from commute_details)
   - Shows nearby POI markers with icons:
     - 🛒 Supermarkets (small cart icon)
     - 🌳 Parks (green tree icon)
     - 💪 Gyms (dumbbell icon)
   - POI markers are smaller/muted, appear only for the selected listing
   - Clear POI markers when card is collapsed

6. **Filter bar (top of left panel or collapsible sidebar):**
   - Price range slider
   - Room count filter
   - Max commute time
   - Amenity checkboxes
   - District multi-select
   - Show saved only / Show applied only
   - Sort by: AI Score / Price / Commute / Newest
   - Filters update both the listing cards AND map markers in real-time
   - All filters via URL params (shareable, bookmarkable)

**Deliverable:** Fully interactive split view — browse listings, see them on map, expand for details, view transit routes and nearby POIs.

---

### SESSION 6 — District Guide & Application Tracker
**Goal:** District guide page and application tracking features.

**Tasks:**
1. **districts.html:**
   - Card for each recommended district
   - Info: character, safety feel, nature/parks, SL lines, avg rent range
   - Match score vs user preferences (simple calculation from settings)
   - "Show listings in this district" button → navigates to listings page with district filter

2. **AI district recommendation:**
   - Button: "Ask AI which district suits us best"
   - Sends user preferences to Claude API
   - Returns top 3 districts with reasoning
   - Displayed as highlighted recommendation card

3. **Application tracker (in listings page):**
   - Filter: "Applied" tab shows only listings with application_status != "not_applied"
   - Status dropdown on listing card (not_applied / applied / waiting / rejected / accepted)
   - Date applied field (auto-set when status changes to "applied")
   - Visual status badges (color-coded)
   - Simple count summary: "3 applied, 1 waiting, 1 accepted"

**Deliverable:** District guide with AI recommendations + application tracking.

---

### SESSION 7 — Polish, Export & Dark Mode
**Goal:** Final quality-of-life features and cleanup.

**Tasks:**
1. **Dark/Light mode:**
   - Toggle in navbar (sun/moon icon) + saved in UserSettings
   - CSS variables for all colors (Tailwind dark: classes)
   - Respect system preference on first visit
   - Leaflet map in split view: switch between light/dark tile layers

2. **Export:**
   - Export saved listings to CSV
   - Include: title, address, price, rooms, AI score, commute, status, notes
   - Download button on listings page

3. **Notifications (simple):**
   - After scrape, show count of new listings found (toast)
   - Badge on navbar if unscored listings exist

4. **UI polish:**
   - Mobile responsive (Tailwind breakpoints)
   - Loading spinners for scrape/AI/enrichment actions
   - Empty states with helpful messages and CTAs
   - Confirm dialogs for destructive actions
   - Consistent toast notifications for success/error

5. **README.md:**
   - How to install (Python, Playwright browsers, .env setup)
   - How to get API keys (Trafiklab, Anthropic required; Google Maps optional)
   - How to run (`flask run` or `python app.py`)
   - How to seed sample data
   - Feature overview

**Deliverable:** Polished, fully usable app with dark mode, export, and good UX.

---

## API Key Setup Instructions

### Trafiklab (Free — Required)
Trafiklab issues a **separate API key per API product**. You need two keys.

1. Go to trafiklab.se → Register free account
2. Create a project → Add these two APIs:
   - **ResRobot v2.1** — journey planning (commute calculation). Bronze: 25 000 req/30d.
     → env var: `TRAFIKLAB_RESROBOT_KEY`
   - **Stops data** — nearby stops lookup. Bronze: 50 req/30d (very limited — cache aggressively).
     → env var: `TRAFIKLAB_STOPS_KEY`
3. Each API generates its own key — copy each separately into `.env`
4. Bronze tier is free and sufficient for personal use

### Anthropic Claude API (Required)
1. Go to console.anthropic.com
2. API Keys → Create key
3. Use model: claude-sonnet-4-20250514

### Google Maps API (Optional — better geocoding accuracy)
1. Go to console.cloud.google.com
2. Create project → Enable: Geocoding API, Directions API
3. Create API key → restrict to your IP
4. If not set, app uses OpenStreetMap Nominatim for free geocoding (works fine for most Stockholm addresses)

---

## Notes for Claude Code
- Always load user settings from DB, never hardcode preferences
- All scraping: randomized 2-5s delays between requests, respect Retry-After headers, cap 50 listings/run
- Use .env for all secrets, never commit .env
- SQLite file stored at: ./database/apartment_finder.db
- UNIQUE constraint on Listing.url — handle IntegrityError gracefully on duplicate inserts
- Flask debug mode ON during development, OFF for any sharing
- Leaflet.js loaded from CDN (no npm needed)
- Tailwind CSS loaded from CDN (no build step needed)
- App must run with zero API keys — manual entry, seed data, and basic UI always work
- Geocoding: check for GOOGLE_MAPS_API_KEY → if set use Google, else use Nominatim (1 req/s, User-Agent required)
- All API calls: try/except with timeouts, never crash the app
- AI scoring: json.loads in try/except, retry once on failure, batch 5 at a time
- Keep each session focused — don't jump ahead to next session's tasks
- When in doubt, prefer simplicity over features
