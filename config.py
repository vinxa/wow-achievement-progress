# config.py
import os

class Config:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5001))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"