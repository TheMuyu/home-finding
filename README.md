# Stockholm Apartment Finder

A Flask web app to find and evaluate rental apartments in Stockholm.
Scrapes listings from Qasa.com, scores them with Claude AI, calculates commute times via Trafiklab SL, and displays everything in an interactive split-view map interface.

---

## Features

- **Scrape listings** from Qasa.com (bulk scrape or paste a single URL)
- **Manual entry** for listings from any source
- **AI scoring** — Claude scores each listing 0–100 with pros, cons, and a summary
- **Commute calculation** — Trafiklab SL journey planner (public transit times to your workplace)
- **Nearby POIs** — supermarkets, parks, gyms via OpenStreetMap Overpass (free, no key)
- **Interactive map** — Leaflet.js with color-coded markers, POI overlays, transit route visualization
- **District guide** — info on recommended Stockholm neighborhoods, AI-powered district recommendation
- **Application tracker** — track which listings you've applied to, waiting, rejected, accepted
- **CSV export** — download all listings as a spreadsheet
- **Dark/light mode** — saved per-user, respects system preference on first visit
- **Works with zero API keys** — seed data and manual entry always work

---

## Installation

### 1. Prerequisites

- Python 3.11+
- pip

### 2. Clone and set up

```bash
git clone <repo-url>
cd home-finding
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Playwright browsers (needed for Qasa scraping)

```bash
playwright install chromium
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your API keys (see API Key Setup below).

### 5. Run the app

```bash
python app.py
```

Open http://localhost:5000 in your browser.

To populate sample listings without needing any API keys:

```bash
python seed_data.py
```

Or click **Seed** on the listings page.

---

## API Key Setup

The app runs with zero API keys (seed data + manual entry + basic UI). Each key unlocks additional features.

### Trafiklab — commute times (required for transit data)

Trafiklab issues a **separate key per API product**. You need two.

1. Register free at [trafiklab.se](https://trafiklab.se)
2. Create a project → Add these two APIs:
   - **ResRobot v2.1** — journey planning. Bronze: 25,000 req/30 days.
   - **Stops Data** — nearby transit stops. Bronze: 50 req/30 days (cache aggressively).
3. Copy each key into `.env`:

```
TRAFIKLAB_RESROBOT_KEY=your_resrobot_key
TRAFIKLAB_STOPS_KEY=your_stops_key
```

### Anthropic Claude — AI scoring (required for AI features)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. API Keys → Create key
3. Add to `.env`:

```
ANTHROPIC_API_KEY=your_anthropic_key
```

### Google Maps — optional, better geocoding accuracy

Without this key the app uses OpenStreetMap Nominatim (free, works well for Stockholm addresses).

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → Enable: Geocoding API, Directions API
3. Create an API key (restrict to your IP for safety)
4. Add to `.env`:

```
GOOGLE_MAPS_API_KEY=your_google_key
```

---

## Usage

### Adding listings

**Option A — Paste a Qasa URL:**
Click **+ Add Listing** → paste a `qasa.com` URL → the app extracts all details automatically → review and save.

**Option B — Manual entry:**
Click **+ Add Listing** → switch to "Enter manually" → fill in the form.

**Option C — Bulk scrape:**
Click **Refresh** on the listings page → scrapes up to 50 listings from Qasa using your budget/rooms settings.

### Scoring listings

- Click **Score with AI** on an individual listing card.
- Click **Score All** to batch-score all unscored listings.
- A badge on the **Listings** nav link shows how many listings are unscored.

### Commute & enrichment

After saving a listing, click **Enrich** (or it runs automatically) to geocode the address, calculate the commute to your work address, and fetch nearby POIs.

Set your work address in **Settings** first.

### Exporting

Click the **CSV** button on the listings page to download all listings as a spreadsheet (title, address, price, rooms, AI score, commute, application status, notes, URL).

### Application tracking

In each listing's expanded detail view, use the **Application status** dropdown to track: Not applied → Applied → Waiting → Rejected / Accepted.

---

## Project Structure

```
home-finding/
├── app.py                  # Flask entry point
├── config.py               # API keys, app config
├── seed_data.py            # Seed 8-10 fake listings
├── database/
│   ├── models.py           # SQLAlchemy models (Listing, UserSettings)
│   └── db.py               # DB init (SQLite at database/apartment_finder.db)
├── scrapers/
│   └── qasa.py             # Qasa.com Playwright scraper
├── services/
│   ├── maps.py             # Geocoding (Nominatim or Google Maps)
│   ├── transit.py          # Trafiklab SL API
│   ├── overpass.py         # OpenStreetMap POI queries
│   ├── ai_scorer.py        # Claude AI scoring
│   ├── enrichment.py       # Orchestrates geocode + commute + POIs
│   └── district_advisor.py # Stockholm district data + AI recommendations
├── routes/
│   ├── listings.py         # Listing CRUD, scrape, manual add
│   ├── api.py              # JSON API endpoints (score, enrich, export)
│   └── settings.py         # User preferences
├── templates/
│   ├── base.html           # Navbar, dark mode, flash messages
│   ├── index.html          # Main split-view (listings + map)
│   ├── add_listing.html    # URL paste / manual entry
│   ├── settings.html       # Preferences panel
│   └── districts.html      # District guide
└── static/
    ├── css/style.css
    └── js/
        ├── app.js          # Main app logic
        ├── filters.js      # Filter state
        └── theme.js        # Dark/light mode
```

---

## Tech Stack

- **Backend:** Python 3.11+, Flask, SQLAlchemy, SQLite
- **Frontend:** HTML, Tailwind CSS (CDN), Vanilla JS, Leaflet.js (CDN)
- **Scraping:** Playwright (Chromium)
- **APIs:** Trafiklab SL, Anthropic Claude, OpenStreetMap Nominatim/Overpass, Google Maps (optional)
