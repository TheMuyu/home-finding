"""
Seed data for Stockholm Apartment Finder.
Run with: python seed_data.py
Or via API: POST /api/seed
"""
from datetime import date, timedelta
import random


SEED_LISTINGS = [
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/1",
        "title": "Cozy 2-room apartment in Hägersten",
        "description": (
            "Lugnt beläget 2-rumslägenhet i populära Hägersten. "
            "Nyligen renoverat kök med diskmaskin. Tvättmaskin i lägenheten. "
            "Nära till tunnelbana och grönområden. Balkong mot tyst innergård."
        ),
        "address": "Hägerstensvägen 42, 129 38 Hägersten",
        "district": "Hägersten",
        "lat": 59.3065,
        "lng": 17.9810,
        "price_sek": 12500,
        "rooms": 2,
        "floor": 3,
        "has_washing_machine": True,
        "has_dryer": False,
        "has_dishwasher": True,
        "size_sqm": 58,
        "available_from": date.today() + timedelta(days=30),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/2",
        "title": "Bright 1-room studio in Midsommarkransen",
        "description": (
            "Fräsch 1-rumslägenhet i trendiga Midsommarkransen. "
            "Öppet planlösning, högt i tak. Gemensam tvättstuga i huset. "
            "Tunnelbana 3 minuters promenad. Mycket lugnt och tryggt område."
        ),
        "address": "Midsommarkransens Torg 8, 126 33 Hägersten",
        "district": "Midsommarkransen",
        "lat": 59.3040,
        "lng": 17.9960,
        "price_sek": 9200,
        "rooms": 1,
        "floor": 2,
        "has_washing_machine": False,
        "has_dryer": False,
        "has_dishwasher": False,
        "size_sqm": 38,
        "available_from": date.today() + timedelta(days=15),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/3",
        "title": "Spacious 3-room family apartment in Enskede",
        "description": (
            "Rymlig 3-rumslägenhet i lugna Enskede, perfekt för familj. "
            "Tvättmaskin och torktumlare i lägenheten. Diskmaskin ingår. "
            "Stor balkong, förråd och parkeringsplats. Nära Enskedeparken "
            "och bra skolor."
        ),
        "address": "Enskedevägen 75, 122 63 Enskede",
        "district": "Enskede",
        "lat": 59.2830,
        "lng": 18.0720,
        "price_sek": 17500,
        "rooms": 3,
        "floor": 1,
        "has_washing_machine": True,
        "has_dryer": True,
        "has_dishwasher": True,
        "size_sqm": 84,
        "available_from": date.today() + timedelta(days=45),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/4",
        "title": "Affordable 1-room apartment in Fruängen",
        "description": (
            "Prisvärd 1-rumslägenhet i Fruängen vid tunnelbanans ändstation. "
            "Renoverat badrum 2021. Gemensam tvättstuga. Lugnt bostadsområde "
            "med närhet till naturreservat och pendling mot city."
        ),
        "address": "Fruängsvägen 12, 129 52 Hägersten",
        "district": "Fruängen",
        "lat": 59.2850,
        "lng": 17.9540,
        "price_sek": 8100,
        "rooms": 1,
        "floor": 4,
        "has_washing_machine": False,
        "has_dryer": False,
        "has_dishwasher": False,
        "size_sqm": 34,
        "available_from": date.today() + timedelta(days=20),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/5",
        "title": "Modern 2-room apartment in Bandhagen",
        "description": (
            "Modernt renoverad 2-rumslägenhet i Bandhagen. Nytt kök med diskmaskin "
            "och induktionshäll. Tvättmaskin i lägenheten. Sydvänd balkong. "
            "Nära Bandhagsparken och tunnelbana mot Gullmarsplan."
        ),
        "address": "Bandhagsvägen 34, 124 61 Bandhagen",
        "district": "Bandhagen",
        "lat": 59.2720,
        "lng": 18.0520,
        "price_sek": 11800,
        "rooms": 2,
        "floor": 2,
        "has_washing_machine": True,
        "has_dryer": False,
        "has_dishwasher": True,
        "size_sqm": 54,
        "available_from": date.today() + timedelta(days=10),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/6",
        "title": "Quiet 2-room apartment in Stureby",
        "description": (
            "Trivsam 2-rumslägenhet i lugna Stureby. Genomgående lägenhet med bra "
            "ljusinsläpp. Gemensam tvättstuga med torkrum. Naturnära med "
            "Sturebyskogens naturreservat i närheten. Pendeltåg 10 min bort."
        ),
        "address": "Sturebyvägen 56, 122 41 Enskede",
        "district": "Stureby",
        "lat": 59.2740,
        "lng": 18.0830,
        "price_sek": 10400,
        "rooms": 2,
        "floor": 1,
        "has_washing_machine": False,
        "has_dryer": False,
        "has_dishwasher": False,
        "size_sqm": 52,
        "available_from": date.today() + timedelta(days=60),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/7",
        "title": "Nature-view 3-room apartment in Björkhagen",
        "description": (
            "Underbar 3-rumslägenhet i Björkhagen med utsikt mot Björkhagens sjö. "
            "Tvättmaskin och torktumlare i lägenheten. Stor hall och förråd. "
            "Barnvänligt område med närheten till Nackareservatet. "
            "Tunnelbana Björkhagen 5 min promenad."
        ),
        "address": "Björkhagsvägen 18, 121 52 Johanneshov",
        "district": "Björkhagen",
        "lat": 59.2930,
        "lng": 18.1100,
        "price_sek": 15900,
        "rooms": 3,
        "floor": 3,
        "has_washing_machine": True,
        "has_dryer": True,
        "has_dishwasher": False,
        "size_sqm": 76,
        "available_from": date.today() + timedelta(days=35),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/8",
        "title": "Charming 2-room apartment in Älvsjö",
        "description": (
            "Charmig 2-rumslägenhet i populära Älvsjö nära pendeltågsstationen. "
            "Renoverat kök 2022. Gemensam tvättstuga i källarplan. Lugnt "
            "och tryggt villakvarter. Nära Älvsjöskogen för naturpromenader."
        ),
        "address": "Älvsjövägen 28, 125 30 Älvsjö",
        "district": "Älvsjö",
        "lat": 59.2670,
        "lng": 17.9880,
        "price_sek": 11200,
        "rooms": 2,
        "floor": 2,
        "has_washing_machine": False,
        "has_dryer": False,
        "has_dishwasher": False,
        "size_sqm": 55,
        "available_from": date.today() + timedelta(days=25),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/9",
        "title": "Top-floor 1-room with terrace in Hägersten",
        "description": (
            "Unikt toppvåningslägenhet med privat terrass i Hägersten. "
            "Diskmaskin i köket. Fantastisk utsikt. Gemensam tvättstuga. "
            "Nära Telefonplan och Liljeholmen för shopping och nöjesliv."
        ),
        "address": "Tellusborgsvägen 90, 126 29 Hägersten",
        "district": "Hägersten",
        "lat": 59.3090,
        "lng": 18.0020,
        "price_sek": 13800,
        "rooms": 1,
        "floor": 6,
        "has_washing_machine": False,
        "has_dryer": False,
        "has_dishwasher": True,
        "size_sqm": 42,
        "available_from": date.today() + timedelta(days=50),
    },
    {
        "source": "seed",
        "url": "https://seed.example.com/listing/10",
        "title": "Large 3-room apartment in Midsommarkransen",
        "description": (
            "Stor och ljus 3-rumslägenhet i hjärtat av Midsommarkransen. "
            "Fullutrustat kök med diskmaskin. Tvättmaskin och torktumlare. "
            "Två balkonger. Nyrenoverat badrum. Tunnelbana 2 min promenad. "
            "Perfekt för par eller liten familj."
        ),
        "address": "Kransvägen 15, 126 35 Hägersten",
        "district": "Midsommarkransen",
        "lat": 59.3055,
        "lng": 17.9980,
        "price_sek": 18000,
        "rooms": 3,
        "floor": 4,
        "has_washing_machine": True,
        "has_dryer": True,
        "has_dishwasher": True,
        "size_sqm": 82,
        "available_from": date.today() + timedelta(days=40),
    },
]


def seed_listings():
    """Seed the database with fake listings. Returns count of newly added listings."""
    # Import inside function to work both as module and standalone script
    from app import create_app
    from database.db import db
    from database.models import Listing
    from sqlalchemy.exc import IntegrityError

    app = create_app()
    added = 0
    with app.app_context():
        for data in SEED_LISTINGS:
            existing = Listing.query.filter_by(url=data["url"]).first()
            if existing:
                continue
            listing = Listing(**data)
            db.session.add(listing)
            try:
                db.session.commit()
                added += 1
            except IntegrityError:
                db.session.rollback()
    return added


def clear_seed_data():
    """Remove all seed listings. Returns count of deleted listings."""
    from app import create_app
    from database.db import db
    from database.models import Listing

    app = create_app()
    with app.app_context():
        deleted = Listing.query.filter_by(source="seed").delete()
        db.session.commit()
    return deleted


if __name__ == "__main__":
    count = seed_listings()
    print(f"Seeded {count} listings.")
