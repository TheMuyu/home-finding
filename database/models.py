from datetime import datetime
from .db import db


class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id = db.Column(db.Integer, primary_key=True)
    work_address = db.Column(db.String(500), nullable=True)
    work_lat = db.Column(db.Float, nullable=True)
    work_lng = db.Column(db.Float, nullable=True)
    budget_min = db.Column(db.Integer, default=5000)
    budget_max = db.Column(db.Integer, default=25000)
    min_rooms = db.Column(db.Integer, default=1)
    max_rooms = db.Column(db.Integer, default=3)
    floor_min = db.Column(db.Integer, nullable=True)
    must_have_washing_machine = db.Column(db.Boolean, default=False)
    must_have_dryer = db.Column(db.Boolean, default=False)
    must_have_dishwasher = db.Column(db.Boolean, default=False)
    must_have_amenities = db.Column(db.JSON, default=list)
    preferred_districts = db.Column(db.JSON, default=list)
    max_commute_minutes = db.Column(db.Integer, default=45)
    theme = db.Column(db.String(10), default="light")

    def to_dict(self):
        return {
            "id": self.id,
            "work_address": self.work_address,
            "work_lat": self.work_lat,
            "work_lng": self.work_lng,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "min_rooms": self.min_rooms,
            "max_rooms": self.max_rooms,
            "floor_min": self.floor_min,
            "must_have_washing_machine": self.must_have_washing_machine,
            "must_have_dryer": self.must_have_dryer,
            "must_have_dishwasher": self.must_have_dishwasher,
            "must_have_amenities": self.must_have_amenities or [],
            "preferred_districts": self.preferred_districts or [],
            "max_commute_minutes": self.max_commute_minutes,
            "theme": self.theme,
        }


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(20), nullable=False, default="manual")
    url = db.Column(db.String(1000), unique=True, nullable=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    description_english = db.Column(db.Text, nullable=True)
    description_turkish = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(500), nullable=True)
    district = db.Column(db.String(200), nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    price_sek = db.Column(db.Integer, nullable=False)
    rooms = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.Integer, nullable=True)
    has_washing_machine = db.Column(db.Boolean, default=False)
    has_dryer = db.Column(db.Boolean, default=False)
    has_dishwasher = db.Column(db.Boolean, default=False)
    size_sqm = db.Column(db.Integer, nullable=True)
    available_from = db.Column(db.String(50), nullable=True)
    # date string or "until_further_notice"
    available_until = db.Column(db.String(50), nullable=True)
    images = db.Column(db.JSON, default=list)
    # Listing character
    # apartment, house, terrace_house, cottage, dorm, other
    home_type = db.Column(db.String(30), nullable=True)
    # furnished, unfurnished, partially_furnished
    furnishing = db.Column(db.String(30), nullable=True)
    # True=shared home, False=entire home
    is_shared = db.Column(db.Boolean, nullable=True)
    # Rent breakdown
    # Qasa service fee on top of rent
    service_fee_sek = db.Column(db.Integer, nullable=True)
    electricity_included = db.Column(db.Boolean, nullable=True)
    deposit_months = db.Column(db.Integer, nullable=True)
    # House rules (JSON: {pets_allowed, smoking_allowed, wheelchair_accessible, max_tenants})
    house_rules = db.Column(db.JSON, default=dict)
    # All detected amenities as a list of keys, e.g. ["balcony","fridge","washing_machine"]
    amenities = db.Column(db.JSON, default=list)
    commute_minutes = db.Column(db.Integer, nullable=True)
    commute_details = db.Column(db.JSON, default=dict)
    transit_route = db.Column(db.JSON, default=dict)
    nearby_stops = db.Column(db.JSON, default=list)
    nearby_pois = db.Column(db.JSON, default=dict)
    ai_score = db.Column(db.Integer, nullable=True)
    ai_comment = db.Column(db.Text, nullable=True)
    ai_pros = db.Column(db.JSON, default=list)
    ai_cons = db.Column(db.JSON, default=list)
    is_saved = db.Column(db.Boolean, default=False)
    application_status = db.Column(
        db.String(20), nullable=True, default="not_applied")
    application_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "description_english": self.description_english,
            "description_turkish": self.description_turkish,
            "address": self.address,
            "district": self.district,
            "lat": self.lat,
            "lng": self.lng,
            "price_sek": self.price_sek,
            "rooms": self.rooms,
            "floor": self.floor,
            "has_washing_machine": self.has_washing_machine,
            "has_dryer": self.has_dryer,
            "has_dishwasher": self.has_dishwasher,
            "size_sqm": self.size_sqm,
            "available_from": self.available_from,
            "available_until": self.available_until,
            "images": self.images or [],
            "home_type": self.home_type,
            "furnishing": self.furnishing,
            "is_shared": self.is_shared,
            "service_fee_sek": self.service_fee_sek,
            "electricity_included": self.electricity_included,
            "deposit_months": self.deposit_months,
            "house_rules": self.house_rules or {},
            "amenities": self.amenities or [],
            "commute_minutes": self.commute_minutes,
            "commute_details": self.commute_details or {},
            "nearby_stops": self.nearby_stops or [],
            "nearby_pois": self.nearby_pois or {},
            "ai_score": self.ai_score,
            "ai_comment": self.ai_comment,
            "ai_pros": self.ai_pros or [],
            "ai_cons": self.ai_cons or [],
            "is_saved": self.is_saved,
            "application_status": self.application_status,
            "application_date": self.application_date.isoformat() if self.application_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
