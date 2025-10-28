# app.py
import asyncio
import threading
from config import Config
from flask import Flask
from services.rate_limiter import limiter
from apscheduler.schedulers.background import BackgroundScheduler
from services.helpers import refresh_achievement_data
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    limiter.init_app(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    from routes import routes_bp
    app.register_blueprint(routes_bp)

    from flask_limiter.errors import RateLimitExceeded
    @app.errorhandler(RateLimitExceeded)
    def ratelimit_handler(e):
        return {"error": "Rate limit exceeded"}, 429
    
    scheduler = BackgroundScheduler()
    def schedule_achievement_data_refresh():
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(refresh_achievement_data())
        else:
            asyncio.run(refresh_achievement_data())

    scheduler.add_job(func=schedule_achievement_data_refresh, trigger="interval", weeks=1)
    scheduler.start()

    print("[SCHEDULER] Running cache refresh on startup...")
    threading.Thread(target=schedule_achievement_data_refresh, daemon=True).start()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)