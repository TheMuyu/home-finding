"""
Stockholm district data for AI scoring context.
Static profiles — no API calls needed.
Data updated April 2026 based on current rental market and SL network.
"""

DISTRICTS = {
    "Hägersten": {
        "description": "Calm, residential southwestern district with good Red Line metro access. Mix of older apartment blocks and villas; part of Hägersten-Liljeholmen borough.",
        "pros": ["Quiet residential feel", "Red Line metro (3 stations)", "Plenty of green corridors", "Family-friendly"],
        "cons": ["Far from central Stockholm (~20 min to T-Centralen)", "Fewer nightlife options"],
        "avg_price_range": "8 500–11 000",
        "sl_lines": ["Metro red line T14", "Midsommarkransen / Hägerstensåsen / Axelsberg stations", "Bus connections"],
        "green_score": 7,
        "safety_note": "Low crime area, considered safe. General Söderort profile.",
    },
    "Älvsjö": {
        "description": "Quiet southern suburb surrounded by the Älvsjöskogen nature reserve (internationally recognised Quiet Park). Currently served by commuter rail; Yellow Line metro arrives in 2034.",
        "pros": ["Älvsjöskogen nature reserve on the doorstep", "Peaceful suburban atmosphere", "Pendeltåg commuter rail direct to city", "Future Yellow Line will boost connectivity (2034)"],
        "cons": ["Limited nightlife and dining", "Feels suburban; fewer services", "Yellow Line still ~8 years away"],
        "avg_price_range": "9 000–12 000",
        "sl_lines": ["Pendeltåg (Nynäs line)", "Bus connections", "Yellow Line T25 coming 2034"],
        "green_score": 9,
        "safety_note": "Very safe. Low crime area consistent with outer residential districts.",
    },
    "Enskede": {
        "description": "Classic garden-city neighbourhood built 1904, with distinctive wooden villas and crooked tree-lined streets. One of Stockholm's most charming residential areas, close to Skogskyrkogården UNESCO site.",
        "pros": ["Safe and calm, very family-friendly", "UNESCO Skogskyrkogården cemetery and park nearby", "Classic Stockholm architecture and character", "Good community feel with local shops"],
        "cons": ["Slightly higher rents than outer suburbs", "Fewer metro stations than some districts"],
        "avg_price_range": "10 000–14 000",
        "sl_lines": ["Metro green line T18", "Enskede gård / Sandsborg / Skogskyrkogården stations", "Bus"],
        "green_score": 8,
        "safety_note": "Safe and family-friendly. Low crime index for the borough.",
    },
    "Midsommarkransen": {
        "description": "Sought-after southwestern suburb with a creative and community-oriented vibe. Very close to Södermalm, giving it an urban feel while staying calmer and more affordable.",
        "pros": ["Vibrant local café and arts scene", "Red Line metro — direct to Slussen in ~10 min", "Strong community feel", "More affordable than Södermalm"],
        "cons": ["Pricier than neighbouring outer suburbs", "Parking is limited", "Smaller green spaces"],
        "avg_price_range": "11 000–15 000",
        "sl_lines": ["Metro red line T14", "Midsommarkransen station"],
        "green_score": 6,
        "safety_note": "Generally safe, low crime. No major concerns.",
    },
    "Fruängen": {
        "description": "Affordable southern terminus of the Red Line with a relaxed, multicultural community. The metro station sits 47 metres above sea level — Stockholm's highest.",
        "pros": ["Affordable rents", "Red Line terminus — direct train to city centre", "Good local amenities and supermarkets", "Multicultural food scene"],
        "cons": ["Less greenery than neighbouring Hägersten", "The commercial strip around the metro can feel busy"],
        "avg_price_range": "9 000–12 000",
        "sl_lines": ["Metro red line T14 (terminus)", "Fruängen station (highest metro station in Stockholm, 47m)"],
        "green_score": 5,
        "safety_note": "Generally safe. Minor incidents near metro terminus occasionally reported.",
    },
    "Bandhagen": {
        "description": "Calm, affordable residential suburb south of the city on the Green Line. Will gain a direct Blue Line connection when the extension opens around 2030.",
        "pros": ["Quiet residential streets", "Green Line metro access", "Affordable rents", "Blue Line extension expected ~2030"],
        "cons": ["Fewer amenities than inner suburbs", "Less green than Älvsjö or Björkhagen"],
        "avg_price_range": "9 000–11 500",
        "sl_lines": ["Metro green line T18/T19", "Bandhagen station", "Blue Line T11 extension ~2030"],
        "green_score": 6,
        "safety_note": "Safe area with low crime. Stable family neighbourhood.",
    },
    "Stureby": {
        "description": "Small, quiet residential neighbourhood with a village-like character. Green Line station opened 1953; the Blue Line extension will take over this station around 2030.",
        "pros": ["Very peaceful and residential", "Green surroundings", "Safe area", "Blue Line upgrade coming ~2030"],
        "cons": ["Limited shops and services", "Current train frequency lower than inner suburbs"],
        "avg_price_range": "9 000–11 000",
        "sl_lines": ["Metro green line T17", "Stureby station", "Blue Line T11 extension ~2030"],
        "green_score": 8,
        "safety_note": "Very safe, consistently low crime figures.",
    },
    "Björkhagen": {
        "description": "Nature-rich district on Stockholm's southeastern edge, with forests and lake swimming spots. Green Line station opened 1958.",
        "pros": ["Beautiful nature and forest walks", "Lake swimming in summer", "Very calm residential feel", "Green Line metro to Slussen in ~15 min"],
        "cons": ["Far from central Stockholm", "Limited nightlife and dining options"],
        "avg_price_range": "9 500–12 000",
        "sl_lines": ["Metro green line T17/T18", "Björkhagen station"],
        "green_score": 10,
        "safety_note": "Very safe. One of the calmer outer residential districts.",
    },
    "Södermalm": {
        "description": "Stockholm's most popular inner-city island — vibrant, trendy, and centrally located. The SoFo neighbourhood (south of Folkungagatan) is a hub for independent shops, restaurants, and nightlife.",
        "pros": ["Central location — everything within walking distance", "Excellent restaurants, bars, and culture", "Multiple metro lines", "Waterfront parks with city views"],
        "cons": ["Expensive rents (highest outside Östermalm)", "Noisy in places (Medborgarplatsen, Slussen)", "Parking nearly impossible"],
        "avg_price_range": "15 000–24 000",
        "sl_lines": ["Metro red line T13: Slussen, Mariatorget, Zinkensdamm, Hornstull", "Metro green line: Slussen", "Blue Line T11 extension: Sofia station (new, ~2030)"],
        "green_score": 4,
        "safety_note": "Generally safe; some petty theft near Medborgarplatsen and Slussen. Central area crime profile.",
    },
    "Vasastan": {
        "description": "Upscale central district famous for its grand 19th-century apartment buildings and leafy streets. Consistently in highest demand among Stockholm renters.",
        "pros": ["Beautiful 19th-century architecture", "Central location near T-Centralen", "Excellent schools and restaurants", "Vasa Park and Observatorielunden nearby"],
        "cons": ["Very expensive", "Busy streets, especially around Odenplan"],
        "avg_price_range": "14 000–22 000",
        "sl_lines": ["Metro green line T17/T18/T19: Odenplan station", "Bus connections"],
        "green_score": 5,
        "safety_note": "Safe area. Low crime consistent with central residential districts.",
    },
    "Kungsholmen": {
        "description": "Island district west of the Old Town, combining excellent waterfront access with calm residential streets. Home to Stockholm City Hall.",
        "pros": ["Excellent Blue Line metro access", "Waterfront parks (Rålambshovsparken, Långholmen)", "Central location", "Strong community amenities"],
        "cons": ["Expensive rents", "Limited greenery compared to southern suburbs"],
        "avg_price_range": "14 000–22 000",
        "sl_lines": ["Metro blue line T10/T11: Rådhuset, Fridhemsplan, Stadshagen", "Bus connections"],
        "green_score": 6,
        "safety_note": "Safe area. Low crime compared to other central districts.",
    },
    "Hökarängen": {
        "description": "One of Stockholm's first planned post-WWII suburbs (1950), built around the very first stretch of the Stockholm metro. Quiet, established community with a strong local identity.",
        "pros": ["Affordable rents", "Green Line metro access", "Good family atmosphere", "Historic first-generation metro suburb"],
        "cons": ["Far from centre (~7.7 km to Slussen)", "Limited nightlife", "Older housing stock"],
        "avg_price_range": "8 000–10 500",
        "sl_lines": ["Metro green line T18", "Hökarängen station (opened October 1950 — one of Stockholm's first metro stations)"],
        "green_score": 6,
        "safety_note": "Safe family district. Generally low crime.",
    },
    "Högdalen": {
        "description": "Multicultural southern suburb with affordable rents and good metro access. Will benefit from the Blue Line extension around 2030 which takes over this Green Line station.",
        "pros": ["Affordable rents", "Green Line metro access", "Multicultural food scene", "Blue Line upgrade coming ~2030"],
        "cons": ["Higher crime index than some outer suburbs — check current local data", "Less green than nearby districts"],
        "avg_price_range": "8 500–10 500",
        "sl_lines": ["Metro green line T18/T19", "Högdalen station", "Blue Line T11 extension ~2030"],
        "green_score": 4,
        "safety_note": "Some crime incidents reported historically. Check current Stockholm police data for the area.",
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
