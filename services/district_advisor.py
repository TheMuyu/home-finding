"""
Stockholm district data for AI scoring context.
Static profiles — no API calls needed.
"""

DISTRICTS = {
    "Hägersten": {
        "description": "Calm and green southwestern district with good transport links.",
        "pros": ["Quiet residential feel", "Plenty of green space", "Good SL metro access", "Family-friendly"],
        "cons": ["Far from central Stockholm", "Fewer nightlife options"],
        "avg_price_range": "10 000–15 000 SEK",
        "sl_lines": ["Metro green line", "Bus connections"],
        "green_score": 8,
        "safety_note": "Low crime area, considered safe.",
    },
    "Älvsjö": {
        "description": "Quiet southern suburb with nature reserves and good commuter rail access.",
        "pros": ["Nature and forests nearby", "Peaceful atmosphere", "Pendeltåg commuter rail"],
        "cons": ["Limited nightlife", "Feels suburban"],
        "avg_price_range": "9 000–13 000 SEK",
        "sl_lines": ["Pendeltåg (commuter rail)", "Bus"],
        "green_score": 9,
        "safety_note": "Very safe area.",
    },
    "Enskede": {
        "description": "Classic Stockholm residential area with parks and a village feel.",
        "pros": ["Safe and calm", "Parks and lakes nearby", "Classic Stockholm architecture", "Good community feel"],
        "cons": ["Slightly limited metro access", "Higher rents vs outer suburbs"],
        "avg_price_range": "11 000–16 000 SEK",
        "sl_lines": ["Metro green line (Enskede Gård)", "Bus"],
        "green_score": 8,
        "safety_note": "Safe and family-friendly.",
    },
    "Midsommarkransen": {
        "description": "Trendy yet calm southwestern district with a creative community.",
        "pros": ["Lively but not hectic", "Good SL metro access", "Cafés and small shops", "Community vibe"],
        "cons": ["Can be pricier than neighbouring areas", "Parking is limited"],
        "avg_price_range": "12 000–17 000 SEK",
        "sl_lines": ["Metro green line"],
        "green_score": 6,
        "safety_note": "Generally safe, low crime.",
    },
    "Fruängen": {
        "description": "Affordable southwestern district with good metro access and a multicultural community.",
        "pros": ["Affordable rents", "Metro terminus (green line)", "Good amenities", "Multicultural"],
        "cons": ["Less greenery than neighbouring areas", "Commercial area around metro can feel busy"],
        "avg_price_range": "9 000–13 000 SEK",
        "sl_lines": ["Metro green line (terminus)"],
        "green_score": 5,
        "safety_note": "Generally safe; some minor incidents near the metro.",
    },
    "Bandhagen": {
        "description": "Calm residential area south of the city, similar character to Högdalen.",
        "pros": ["Quiet residential streets", "Good metro access", "Affordable"],
        "cons": ["Few amenities compared to inner suburbs", "Less green than Älvsjö"],
        "avg_price_range": "9 000–13 000 SEK",
        "sl_lines": ["Metro red line"],
        "green_score": 6,
        "safety_note": "Safe area with low crime.",
    },
    "Stureby": {
        "description": "Small, quiet residential neighbourhood with a village-like atmosphere.",
        "pros": ["Very peaceful", "Green surroundings", "Safe"],
        "cons": ["Limited shops and services", "Fewer transit options"],
        "avg_price_range": "9 000–13 000 SEK",
        "sl_lines": ["Bus connections to metro"],
        "green_score": 8,
        "safety_note": "Very safe, low crime.",
    },
    "Björkhagen": {
        "description": "Nature-rich district with lakes and forests on Stockholm's southeastern edge.",
        "pros": ["Beautiful nature", "Lakes for swimming", "Very calm", "Good metro access"],
        "cons": ["Far from central Stockholm", "Limited nightlife and dining"],
        "avg_price_range": "10 000–14 000 SEK",
        "sl_lines": ["Metro green line"],
        "green_score": 10,
        "safety_note": "Very safe area.",
    },
    "Södermalm": {
        "description": "Vibrant inner-city island, Stockholm's most popular hip neighbourhood.",
        "pros": ["Central location", "Excellent restaurants and nightlife", "Great SL access", "Cultural hub"],
        "cons": ["Expensive rents", "Noisy in some parts", "Parking is very limited"],
        "avg_price_range": "15 000–25 000 SEK",
        "sl_lines": ["Metro red/green/blue lines", "Bus"],
        "green_score": 4,
        "safety_note": "Generally safe; some petty crime near Medborgarplatsen.",
    },
    "Vasastan": {
        "description": "Upscale inner-city neighbourhood with beautiful 19th-century buildings.",
        "pros": ["Central", "Beautiful architecture", "Good schools", "Restaurants and cafés"],
        "cons": ["Very expensive", "Busy streets"],
        "avg_price_range": "16 000–28 000 SEK",
        "sl_lines": ["Metro red line", "Bus"],
        "green_score": 5,
        "safety_note": "Safe area.",
    },
    "Kungsholmen": {
        "description": "Island district with a mix of residential and commercial areas near City Hall.",
        "pros": ["Central location", "Waterfront walks", "Good transport"],
        "cons": ["Expensive", "Limited greenery"],
        "avg_price_range": "15 000–26 000 SEK",
        "sl_lines": ["Metro blue line", "Bus"],
        "green_score": 5,
        "safety_note": "Safe area.",
    },
    "Hökarängen": {
        "description": "Southern suburb with a 1950s functionalist character and good community feel.",
        "pros": ["Affordable", "Good metro access", "Local shops and services"],
        "cons": ["Far from centre", "Limited nightlife"],
        "avg_price_range": "9 000–13 000 SEK",
        "sl_lines": ["Metro red line"],
        "green_score": 6,
        "safety_note": "Generally safe.",
    },
    "Högdalen": {
        "description": "Multicultural southern suburb with good metro access and affordable rents.",
        "pros": ["Affordable", "Metro access", "Multicultural food scene"],
        "cons": ["Higher crime index than some areas", "Less green"],
        "avg_price_range": "8 000–12 000 SEK",
        "sl_lines": ["Metro red line"],
        "green_score": 4,
        "safety_note": "Some crime incidents reported; check current local data.",
    },
}


def get_district_profile(district_name: str) -> dict | None:
    """
    Return district profile for the given name, or None if not found.
    Case-insensitive partial match.
    """
    if not district_name:
        return None
    name_lower = district_name.lower()
    for key, profile in DISTRICTS.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return {"name": key, **profile}
    return None


def get_all_districts() -> list[dict]:
    """Return all district profiles as a list."""
    return [{"name": key, **profile} for key, profile in DISTRICTS.items()]
