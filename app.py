# app.py
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)

from routes import routes_bp
app.register_blueprint(routes_bp)

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)