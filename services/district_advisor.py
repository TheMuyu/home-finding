"""
Stockholm district data for AI scoring context.
Static profiles — no API calls needed.
Data updated April 2026 based on current rental market and SL network.
"""

DISTRICTS = {
    "Hägersten": {
        "description": "Calm, residential southwestern district with good Red Line metro access. Mix of older apartment blocks and villas; part of Hägersten-Liljeholmen borough.",
        "description_tr": "Kırmızı Hat metrosu ile iyi bağlantıya sahip sakin, yerleşik güneybatı ilçesi. Eski apartman blokları ve villalarının karışımından oluşur; Hägersten-Liljeholmen bölgesinin bir parçasıdır.",
        "pros": ["Quiet residential feel", "Red Line metro (3 stations)", "Plenty of green corridors", "Family-friendly"],
        "pros_tr": ["Sakin konut dokusu", "Kırmızı Hat metrosu (3 istasyon)", "Bol yeşil koridorlar", "Aile dostu"],
        "cons": ["Far from central Stockholm (~20 min to T-Centralen)", "Fewer nightlife options"],
        "cons_tr": ["Merkezi Stockholm'den uzak (~T-Centralen'e 20 dakika)", "Gece hayatı seçenekleri az"],
        "avg_price_range": "8 500–11 000",
        "sl_lines": ["Metro red line T14", "Midsommarkransen / Hägerstensåsen / Axelsberg stations", "Bus connections"],
        "green_score": 7,
        "safety_note": "Low crime area, considered safe. General Söderort profile.",
        "safety_note_tr": "Suç oranı düşük, güvenli kabul edilir. Genel Söderort profili.",
    },
    "Älvsjö": {
        "description": "Quiet southern suburb surrounded by the Älvsjöskogen nature reserve (internationally recognised Quiet Park). Currently served by commuter rail; Yellow Line metro arrives in 2034.",
        "description_tr": "Uluslararası alanda tanınan Sessiz Park olan Älvsjöskogen doğa rezervi ile çevrili sakin güney banliyösü. Şu anda banliyö treni ile hizmet verilmekte; Sarı Hat metrosu 2034'te geliyor.",
        "pros": ["Älvsjöskogen nature reserve on the doorstep", "Peaceful suburban atmosphere", "Pendeltåg commuter rail direct to city", "Future Yellow Line will boost connectivity (2034)"],
        "pros_tr": ["Kapıda Älvsjöskogen doğa rezervi", "Huzurlu banliyö atmosferi", "Şehir merkezine direkt Pendeltåg banliyö treni", "Gelecekteki Sarı Hat bağlantısı bağlantıyı artıracak (2034)"],
        "cons": ["Limited nightlife and dining", "Feels suburban; fewer services", "Yellow Line still ~8 years away"],
        "cons_tr": ["Sınırlı gece hayatı ve yemek seçenekleri", "Banliyö hissi; daha az hizmet", "Sarı Hat hâlâ ~8 yıl uzakta"],
        "avg_price_range": "9 000–12 000",
        "sl_lines": ["Pendeltåg (Nynäs line)", "Bus connections", "Yellow Line T25 coming 2034"],
        "green_score": 9,
        "safety_note": "Very safe. Low crime area consistent with outer residential districts.",
        "safety_note_tr": "Çok güvenli. Dış yerleşim bölgeleriyle tutarlı düşük suç oranı.",
    },
    "Enskede": {
        "description": "Classic garden-city neighbourhood built 1904, with distinctive wooden villas and crooked tree-lined streets. One of Stockholm's most charming residential areas, close to Skogskyrkogården UNESCO site.",
        "description_tr": "1904'te inşa edilmiş klasik bahçe şehri mahallesi; kendine özgü ahşap villalar ve kıvrımlı ağaçlı sokaklar. Stockholm'ün en büyüleyici konut bölgelerinden biri; yakınında Skogskyrkogården UNESCO alanı var.",
        "pros": ["Safe and calm, very family-friendly", "UNESCO Skogskyrkogården cemetery and park nearby", "Classic Stockholm architecture and character", "Good community feel with local shops"],
        "pros_tr": ["Güvenli ve sakin, çok aile dostu", "Yakınlarda UNESCO Skogskyrkogården mezarlığı ve parkı", "Klasik Stockholm mimarisi ve karakteri", "Yerel dükkanlarla güçlü topluluk hissi"],
        "cons": ["Slightly higher rents than outer suburbs", "Fewer metro stations than some districts"],
        "cons_tr": ["Dış banliyölere kıyasla biraz yüksek kiralar", "Bazı bölgelere göre daha az metro istasyonu"],
        "avg_price_range": "10 000–14 000",
        "sl_lines": ["Metro green line T18", "Enskede gård / Sandsborg / Skogskyrkogården stations", "Bus"],
        "green_score": 8,
        "safety_note": "Safe and family-friendly. Low crime index for the borough.",
        "safety_note_tr": "Güvenli ve aile dostu. Bölge için düşük suç endeksi.",
    },
    "Midsommarkransen": {
        "description": "Sought-after southwestern suburb with a creative and community-oriented vibe. Very close to Södermalm, giving it an urban feel while staying calmer and more affordable.",
        "description_tr": "Yaratıcı ve topluluk odaklı bir yapıya sahip çok aranan güneybatı banliyösü. Södermalm'a çok yakın; daha sakin ve uygun fiyatlı kalırken kentsel bir his veriyor.",
        "pros": ["Vibrant local café and arts scene", "Red Line metro — direct to Slussen in ~10 min", "Strong community feel", "More affordable than Södermalm"],
        "pros_tr": ["Canlı yerel kafe ve sanat ortamı", "Kırmızı Hat metrosu — Slussen'e ~10 dakika direkt", "Güçlü topluluk hissi", "Södermalm'dan daha uygun fiyatlı"],
        "cons": ["Pricier than neighbouring outer suburbs", "Parking is limited", "Smaller green spaces"],
        "cons_tr": ["Komşu dış banliyölerden daha pahalı", "Park yeri kısıtlı", "Yeşil alan az"],
        "avg_price_range": "11 000–15 000",
        "sl_lines": ["Metro red line T14", "Midsommarkransen station"],
        "green_score": 6,
        "safety_note": "Generally safe, low crime. No major concerns.",
        "safety_note_tr": "Genel olarak güvenli, düşük suç oranı. Önemli bir sorun yok.",
    },
    "Fruängen": {
        "description": "Affordable southern terminus of the Red Line with a relaxed, multicultural community. The metro station sits 47 metres above sea level — Stockholm's highest.",
        "description_tr": "Sakin ve çok kültürlü bir topluluğa sahip Kırmızı Hat'ın uygun fiyatlı güney terminusu. Metro istasyonu 47 metre yükseklikte — Stockholm'ün en yüksek metro istasyonu.",
        "pros": ["Affordable rents", "Red Line terminus — direct train to city centre", "Good local amenities and supermarkets", "Multicultural food scene"],
        "pros_tr": ["Uygun fiyatlı kiralar", "Kırmızı Hat terminusu — şehir merkezine direkt tren", "İyi yerel olanaklar ve süpermarketler", "Çok kültürlü yemek sahnesi"],
        "cons": ["Less greenery than neighbouring Hägersten", "The commercial strip around the metro can feel busy"],
        "cons_tr": ["Komşu Hägersten'e kıyasla daha az yeşil alan", "Metro terminusu etrafındaki ticari şerit kalabalık hissettiriyor"],
        "avg_price_range": "9 000–12 000",
        "sl_lines": ["Metro red line T14 (terminus)", "Fruängen station (highest metro station in Stockholm, 47m)"],
        "green_score": 5,
        "safety_note": "Generally safe. Minor incidents near metro terminus occasionally reported.",
        "safety_note_tr": "Genel olarak güvenli. Metro terminusu yakınında zaman zaman küçük olaylar bildiriliyor.",
    },
    "Bandhagen": {
        "description": "Calm, affordable residential suburb south of the city on the Green Line. Will gain a direct Blue Line connection when the extension opens around 2030.",
        "description_tr": "Yeşil Hat üzerinde şehrin güneyinde sakin ve uygun fiyatlı bir yerleşim banliyösü. ~2030'da uzatma açıldığında doğrudan Mavi Hat bağlantısı kazanacak.",
        "pros": ["Quiet residential streets", "Green Line metro access", "Affordable rents", "Blue Line extension expected ~2030"],
        "pros_tr": ["Sakin yerleşim sokakları", "Yeşil Hat metro erişimi", "Uygun fiyatlı kiralar", "~2030'da beklenen Mavi Hat uzatması"],
        "cons": ["Fewer amenities than inner suburbs", "Less green than Älvsjö or Björkhagen"],
        "cons_tr": ["İç banliyölerden daha az olanak", "Älvsjö veya Björkhagen'dan daha az yeşil alan"],
        "avg_price_range": "9 000–11 500",
        "sl_lines": ["Metro green line T18/T19", "Bandhagen station", "Blue Line T11 extension ~2030"],
        "green_score": 6,
        "safety_note": "Safe area with low crime. Stable family neighbourhood.",
        "safety_note_tr": "Suç oranı düşük güvenli bölge. İstikrarlı aile mahallesi.",
    },
    "Stureby": {
        "description": "Small, quiet residential neighbourhood with a village-like character. Green Line station opened 1953; the Blue Line extension will take over this station around 2030.",
        "description_tr": "Köy gibi bir karaktere sahip küçük, sakin bir yerleşim mahallesi. Yeşil Hat istasyonu 1953'te açıldı; Mavi Hat uzatması ~2030 civarında bu istasyonu devralacak.",
        "pros": ["Very peaceful and residential", "Green surroundings", "Safe area", "Blue Line upgrade coming ~2030"],
        "pros_tr": ["Çok huzurlu ve konut niteliğinde", "Yeşil çevre", "Güvenli bölge", "~2030'da Mavi Hat yükseltmesi geliyor"],
        "cons": ["Limited shops and services", "Current train frequency lower than inner suburbs"],
        "cons_tr": ["Sınırlı dükkan ve hizmet", "Mevcut tren sıklığı iç banliyölerden düşük"],
        "avg_price_range": "9 000–11 000",
        "sl_lines": ["Metro green line T17", "Stureby station", "Blue Line T11 extension ~2030"],
        "green_score": 8,
        "safety_note": "Very safe, consistently low crime figures.",
        "safety_note_tr": "Çok güvenli, sürekli düşük suç rakamları.",
    },
    "Björkhagen": {
        "description": "Nature-rich district on Stockholm's southeastern edge, with forests and lake swimming spots. Green Line station opened 1958.",
        "description_tr": "Stockholm'ün güneydoğu kenarında ormanlar ve göl yüzme alanlarıyla doğa zengini bir ilçe. Yeşil Hat istasyonu 1958'de açıldı.",
        "pros": ["Beautiful nature and forest walks", "Lake swimming in summer", "Very calm residential feel", "Green Line metro to Slussen in ~15 min"],
        "pros_tr": ["Güzel doğa ve orman yürüyüşleri", "Yazın göl yüzme imkânı", "Çok sakin konut ortamı", "Yeşil Hat metrosuyla Slussen'e ~15 dakika"],
        "cons": ["Far from central Stockholm", "Limited nightlife and dining options"],
        "cons_tr": ["Merkezi Stockholm'den uzak", "Sınırlı gece hayatı ve yemek seçenekleri"],
        "avg_price_range": "9 500–12 000",
        "sl_lines": ["Metro green line T17/T18", "Björkhagen station"],
        "green_score": 10,
        "safety_note": "Very safe. One of the calmer outer residential districts.",
        "safety_note_tr": "Çok güvenli. En sakin dış yerleşim bölgelerinden biri.",
    },
    "Södermalm": {
        "description": "Stockholm's most popular inner-city island — vibrant, trendy, and centrally located. The SoFo neighbourhood (south of Folkungagatan) is a hub for independent shops, restaurants, and nightlife.",
        "description_tr": "Stockholm'ün en popüler iç şehir adası — canlı, modaya uygun ve merkezi konumda. SoFo mahallesi (Folkungagatan'ın güneyinde) bağımsız dükkanlar, restoranlar ve gece hayatı için bir merkez.",
        "pros": ["Central location — everything within walking distance", "Excellent restaurants, bars, and culture", "Multiple metro lines", "Waterfront parks with city views"],
        "pros_tr": ["Merkezi konum — her şey yürüme mesafesinde", "Mükemmel restoranlar, barlar ve kültür", "Birden fazla metro hattı", "Şehir manzaralı sahil parkları"],
        "cons": ["Expensive rents (highest outside Östermalm)", "Noisy in places (Medborgarplatsen, Slussen)", "Parking nearly impossible"],
        "cons_tr": ["Pahalı kiralar (Östermalm dışında en yüksek)", "Bazı yerlerde gürültülü (Medborgarplatsen, Slussen)", "Park yeri neredeyse imkânsız"],
        "avg_price_range": "15 000–24 000",
        "sl_lines": ["Metro red line T13: Slussen, Mariatorget, Zinkensdamm, Hornstull", "Metro green line: Slussen", "Blue Line T11 extension: Sofia station (new, ~2030)"],
        "green_score": 4,
        "safety_note": "Generally safe; some petty theft near Medborgarplatsen and Slussen. Central area crime profile.",
        "safety_note_tr": "Genel olarak güvenli; Medborgarplatsen ve Slussen yakınlarında bazı yankesicilik vakaları. Merkezi bölge suç profili.",
    },
    "Vasastan": {
        "description": "Upscale central district famous for its grand 19th-century apartment buildings and leafy streets. Consistently in highest demand among Stockholm renters.",
        "description_tr": "Görkemli 19. yüzyıl apartman binaları ve yapraklı sokakları ile tanınan üst sınıf merkezi ilçe. Stockholm kiracıları arasında sürekli en yüksek talep gören bölge.",
        "pros": ["Beautiful 19th-century architecture", "Central location near T-Centralen", "Excellent schools and restaurants", "Vasa Park and Observatorielunden nearby"],
        "pros_tr": ["Güzel 19. yüzyıl mimarisi", "T-Centralen yakınında merkezi konum", "Mükemmel okullar ve restoranlar", "Yakınlarda Vasa Parkı ve Observatorielunden"],
        "cons": ["Very expensive", "Busy streets, especially around Odenplan"],
        "cons_tr": ["Çok pahalı", "Özellikle Odenplan çevresinde yoğun sokaklar"],
        "avg_price_range": "14 000–22 000",
        "sl_lines": ["Metro green line T17/T18/T19: Odenplan station", "Bus connections"],
        "green_score": 5,
        "safety_note": "Safe area. Low crime consistent with central residential districts.",
        "safety_note_tr": "Güvenli bölge. Merkezi konut bölgeleriyle tutarlı düşük suç oranı.",
    },
    "Kungsholmen": {
        "description": "Island district west of the Old Town, combining excellent waterfront access with calm residential streets. Home to Stockholm City Hall.",
        "description_tr": "Eski Şehir'in batısında su kenarına mükemmel erişimi sakin konut sokakları ile birleştiren ada ilçesi. Stockholm Belediye Binası'na ev sahipliği yapar.",
        "pros": ["Excellent Blue Line metro access", "Waterfront parks (Rålambshovsparken, Långholmen)", "Central location", "Strong community amenities"],
        "pros_tr": ["Mükemmel Mavi Hat metro erişimi", "Su kenarı parkları (Rålambshovsparken, Långholmen)", "Merkezi konum", "Güçlü topluluk olanakları"],
        "cons": ["Expensive rents", "Limited greenery compared to southern suburbs"],
        "cons_tr": ["Pahalı kiralar", "Güney banliyölerine kıyasla sınırlı yeşil alan"],
        "avg_price_range": "14 000–22 000",
        "sl_lines": ["Metro blue line T10/T11: Rådhuset, Fridhemsplan, Stadshagen", "Bus connections"],
        "green_score": 6,
        "safety_note": "Safe area. Low crime compared to other central districts.",
        "safety_note_tr": "Güvenli bölge. Diğer merkezi ilçelere kıyasla düşük suç oranı.",
    },
    "Hökarängen": {
        "description": "One of Stockholm's first planned post-WWII suburbs (1950), built around the very first stretch of the Stockholm metro. Quiet, established community with a strong local identity.",
        "description_tr": "Stockholm'ün ilk planlı savaş sonrası banliyölerinden biri (1950); Stockholm metrosunun ilk hattı etrafında inşa edildi. Güçlü yerel kimliğe sahip sakin, köklü topluluk.",
        "pros": ["Affordable rents", "Green Line metro access", "Good family atmosphere", "Historic first-generation metro suburb"],
        "pros_tr": ["Uygun fiyatlı kiralar", "Yeşil Hat metro erişimi", "İyi aile atmosferi", "Tarihi birinci nesil metro banliyösü"],
        "cons": ["Far from centre (~7.7 km to Slussen)", "Limited nightlife", "Older housing stock"],
        "cons_tr": ["Merkezden uzak (~Slussen'e 7,7 km)", "Sınırlı gece hayatı", "Eski konut stoku"],
        "avg_price_range": "8 000–10 500",
        "sl_lines": ["Metro green line T18", "Hökarängen station (opened October 1950 — one of Stockholm's first metro stations)"],
        "green_score": 6,
        "safety_note": "Safe family district. Generally low crime.",
        "safety_note_tr": "Güvenli aile bölgesi. Genel olarak düşük suç oranı.",
    },
    "Högdalen": {
        "description": "Multicultural southern suburb with affordable rents and good metro access. Will benefit from the Blue Line extension around 2030 which takes over this Green Line station.",
        "description_tr": "Uygun fiyatlı kiralar ve iyi metro erişimi olan çok kültürlü güney banliyösü. Bu Yeşil Hat istasyonunu devralan ~2030'daki Mavi Hat uzatmasından yararlanacak.",
        "pros": ["Affordable rents", "Green Line metro access", "Multicultural food scene", "Blue Line upgrade coming ~2030"],
        "pros_tr": ["Uygun fiyatlı kiralar", "Yeşil Hat metro erişimi", "Çok kültürlü yemek sahnesi", "~2030'da Mavi Hat yükseltmesi geliyor"],
        "cons": ["Higher crime index than some outer suburbs — check current local data", "Less green than nearby districts"],
        "cons_tr": ["Bazı dış banliyölerden yüksek suç endeksi — güncel yerel verileri kontrol edin", "Yakın bölgelere kıyasla daha az yeşil alan"],
        "avg_price_range": "8 500–10 500",
        "sl_lines": ["Metro green line T18/T19", "Högdalen station", "Blue Line T11 extension ~2030"],
        "green_score": 4,
        "safety_note": "Some crime incidents reported historically. Check current Stockholm police data for the area.",
        "safety_note_tr": "Tarihsel olarak bazı suç olayları bildirildi. Bölge için güncel Stockholm polis verilerini kontrol edin.",
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
