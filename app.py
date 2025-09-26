# app.py
from config import Config
from flask import Flask
from services.rate_limiter import limiter

app = Flask(__name__)
app.config.from_object(Config)

limiter.init_app(app)

from routes import routes_bp
app.register_blueprint(routes_bp)

from flask_limiter.errors import RateLimitExceeded
@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return {"error": "Rate limit exceeded"}, 429

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)