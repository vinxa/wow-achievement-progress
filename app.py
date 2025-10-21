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
    def schedule_cache_refresh():
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(refresh_server_caches())
        else:
            asyncio.run(refresh_server_caches())

    scheduler.add_job(func=schedule_cache_refresh, trigger="interval", weeks=1)
    scheduler.start()

    print("[SCHEDULER] Running cache refresh on startup...")
    schedule_cache_refresh()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)