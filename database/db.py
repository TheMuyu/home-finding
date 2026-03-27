import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize the database with the Flask app."""
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(db_dir, "apartment_finder.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        # Import models to ensure they are registered before create_all
        from . import models  # noqa: F401
        db.create_all()
