# app.py
import asyncio
from config import Config
from flask import Flask
from services.rate_limiter import limiter
from apscheduler.schedulers.background import BackgroundScheduler
from services.helpers import refresh_server_caches

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    limiter.init_app(app)
    from routes import routes_bp
    app.register_blueprint(routes_bp)

    from flask_limiter.errors import RateLimitExceeded
    @app.errorhandler(RateLimitExceeded)
    def ratelimit_handler(e):
        return {"error": "Rate limit exceeded"}, 429
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=refresh_server_caches, trigger="interval", weeks=1)
    scheduler.start()
    print("[SCHEDULER] Running cache refresh on startup...")
    try:
        asyncio.run(refresh_server_caches())
    except Exception as e:
        print(f"[SCHEDULER] Startup cache refresh failed: {e}")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)