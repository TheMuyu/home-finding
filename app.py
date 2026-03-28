from flask import Flask
from config import FLASK_SECRET_KEY, get_missing_api_keys
from database.db import init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    # Initialize database
    init_db(app)

    # Register blueprints
    from routes.listings import listings_bp
    from routes.api import api_bp
    from routes.settings import settings_bp

    app.register_blueprint(listings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)

    # Inject globals into all templates
    @app.context_processor
    def inject_globals():
        unscored_count = 0
        db_theme = "light"
        try:
            from database.models import Listing, UserSettings
            unscored_count = Listing.query.filter(Listing.ai_score.is_(None)).count()
            settings = UserSettings.query.first()
            if settings:
                db_theme = settings.theme or "light"
        except Exception:
            pass
        return {
            "missing_keys": get_missing_api_keys(),
            "unscored_count": unscored_count,
            "db_theme": db_theme,
        }

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
