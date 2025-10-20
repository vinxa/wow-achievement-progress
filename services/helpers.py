import re
import os
import time
from .realm_api import get_realms
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

TOKEN_URL = "https://oauth.battle.net/token"
_token_cache = {"access_token": None, "expires_at": 0.0}

def fetch_access_token():
    if _token_cache["access_token"] and _token_cache["expires_at"] > time.time():
        return _token_cache["access_token"]
    
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Missing CLIENT_ID or CLIENT_SECRET environment variables")

    data = {"grant_type": "client_credentials"}
    print(f"[DEBUG] Fetching token from {TOKEN_URL}...")
    try:
        resp = requests.post(TOKEN_URL, data=data, auth=HTTPBasicAuth(client_id, client_secret), timeout=10)
        resp.raise_for_status()
        result = resp.json()
        token = result.get("access_token")
        expires_in = result.get("expires_in", 0)
        if not token:
            raise RuntimeError(f"Unexpected token response: {result}")
        _token_cache["access_token"] = token
        _token_cache["expires_at"] = time.time() +  + max(int(expires_in) - 60, 0)  # Expire minute early
        return token
    except Exception as e:
        print(f"[ERROR] Failed to fetch token: {e}")
        return {"error": f"Failed to fetch token: {e}"}

def validate_inputs(server, character, region):
    realms = get_realms(region)

    server_obj = next(
        (r for r in realms if r["slug"].lower() == server.lower() or r["name"].lower() == server.lower()),
        None
    )
    if not server_obj:
        raise ValueError(f"Invalid server: {server}")

    return server_obj["slug"], character, server_obj["name"]


def sanitize_slug(text: str) -> str:
    return re.sub(r'[^A-Za-z0-9-]', '', text)


def iso_to_seconds(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return None