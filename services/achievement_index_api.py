# app/services/blizzard_api.py
import asyncio
import aiohttp
from pathlib import Path
from .helpers import iso_to_seconds, sanitize_slug
import os
import time
import json

AUTH_URL = "https://oauth.battle.net/token"
CACHE_FILE = Path(__file__).parent / "achievements_cache.json"
CACHE_TTL = 24 * 3600
TOKEN_URL = "https://oauth.battle.net/token"

_token_cache = {"access_token": None, "expires_at": 0.0}

def build_achievement_index_url(region):
    region = (region or "us").strip().lower()
    return (
        f"https://{region}.api.blizzard.com/data/wow/achievement/index"
        f"?namespace=static-{region}&locale=en_US"
    )

async def fetch_access_token():
    if _token_cache["access_token"] and _token_cache["expires_at"] > time.time():
        return _token_cache["access_token"]
    
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Missing CLIENT_ID or CLIENT_SECRET environment variables")

    data = {"grant_type": "client_credentials"}
    auth = aiohttp.BasicAuth(client_id, client_secret)
    print(f"[DEBUG] Fetching token from {AUTH_URL}...")
    try:
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(AUTH_URL, data=data) as resp:
                resp.raise_for_status()
                result = await resp.json()
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

async def fetch_achievement_index(region):
    token = await fetch_access_token()
    headers = {"Battlenet-Namespace": "{region}-static", "Authorization": f"Bearer {await fetch_access_token()}"}
    url = build_achievement_index_url(region)
    print(f"Fetching achievements from {url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                result = await resp.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch achievements: {e}")
        return {"error": f"Failed to fetch achievements: {e}"}
    achievements = []
    for entry in result.get("achievements", []):
        ach_id = entry.get("id")
        name = entry.get("name")
        if ach_id and name:
            achievements.append({"id": ach_id, "name": name})
    return achievements
 
def get_static_achievement_index(region):
    # Figure out if we need to refetch index
    now = time.time()
    cache = {}

    if CACHE_FILE.exists() and CACHE_FILE.stat().st_size > 0:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                entry = cache.get(region)
        except Exception as e:
            print("Cache read error:", e)
            cache = {}
        if entry and entry.get("data") and now - entry["timestamp"] < CACHE_TTL:
            print("Loaded achievements from cache")
            return entry["data"]

    achievements = asyncio.run(fetch_achievement_index(region))
    cache[region] = {"timestamp": now, "data": achievements}
    try:
        tmp_file = CACHE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache, f)
        tmp_file.replace(CACHE_FILE)
    except Exception as e:
        print("Cache write error:", e)
    return achievements

def search_achievements(query, region):
    q = (query or "").strip().lower()
    achievements = asyncio.run(get_static_achievement_index(region))
    results = []
    for achievement in achievements:
        if q in achievement["name"].lower():
            results.append(achievement)
    return results