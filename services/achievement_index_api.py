# services/achievement_index_api.py
import asyncio
import aiohttp
import time
import json
from pathlib import Path
from aiolimiter import AsyncLimiter
from .auth_api import fetch_access_token

DROPDOWN_CACHE_FILE = Path(__file__).parent / "achievements_cache.json"
TREE_CACHE_FILE = Path(__file__).parent / "achievement_tree_cache.json"
CACHE_TTL = 24 * 3600 * 7  # 1 week
MAX_RETRIES = 5
RATE_DELAY = 0.2 
CONCURRENT_LIMIT = 5
RATE_LIMIT = AsyncLimiter(5, 1) # 5 per second
CONCURRENCY_SEM = asyncio.Semaphore(CONCURRENT_LIMIT)

async def throttled_req(session, url, headers):
    # AsyncLimiter here as this controls how fast requests leave the process (how many per second). Delay makes it smooth - forces a delay between starts so they aren't all firing at exactly the same time.
    async with RATE_LIMIT:
        await asyncio.sleep(RATE_DELAY)
        return await session.get(url, headers=headers)

async def fetch_json(session, url, headers, attempt=1):
    # Semaphore here to limit concurrency (no more than x requests active at any time.)
    async with CONCURRENCY_SEM:
        try:
            resp = await throttled_req(session, url, headers)
            if resp.status == 429:  # Rate limited
                wait = min(2 ** attempt, 10)
                await asyncio.sleep(wait)
                if attempt < MAX_RETRIES:
                    return await fetch_json(session, url, headers, attempt + 1)
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history, status=429, message="Too Many Requests")
            resp.raise_for_status()
            return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, aiohttp.ServerDisconnectedError) as e:
            if attempt < MAX_RETRIES:
                wait = min(2**attempt, 10)
                print(f"[WARN] {e}. retry {attempt}/{MAX_RETRIES} after {wait:.2f}s")
                await asyncio.sleep(wait)
                return await fetch_json(session, url, headers, attempt + 1)
            print(f"[ERROR] {type(e).__name__}: {e} (giving up)")
            raise

async def fetch_achievement_index(region):
    region = (region or "us").strip().lower()
    token = fetch_access_token()
    url = f"https://{region}.api.blizzard.com/data/wow/achievement/index?namespace=static-{region}&locale=en_US"
    headers = {"Battlenet-Namespace": "{region}-static", "Authorization": f"Bearer {token}"}
    print(f"Fetching achievements from {url}...")
    async with aiohttp.ClientSession() as session:
        try:
            result = await fetch_json(session, url, headers)
        except Exception as e:
            print(f"[ERROR] Failed to fetch achievements: {e}")
            return []
    # achievements = []
    return [{"id": a["id"], "name": a["name"]} for a in result.get("achievements", []) if a.get("id") and a.get("name")]

async def fetch_achievement_details(session, region, ach_id, token):
    url = f"https://{region}.api.blizzard.com/data/wow/achievement/{ach_id}?namespace=static-{region}&locale=en_US"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Fetching achievement {ach_id} details from {url}...")
    try:
        return await fetch_json(session, url, headers)
    except Exception as e:
        print(f"[ERROR] Failed to fetch achievement {ach_id} details: {e}")
        return {"error": f"Failed to fetch {ach_id} details: {e}"}

async def build_achievement_subtree(session, region, ach_id, visited, token):
    if ach_id in visited:
        return {"id": ach_id, "name": "circular reference safety hit :("}
    visited.add(ach_id)

    details = await fetch_achievement_details(session, region, ach_id, token)
    if not details or "error" in details:
        return {"error": f"Failed to fetch achievement {ach_id} details: {details.get('error')}"}
    
    node = {"id": details.get("id"), "name": details.get("name"), "criteria": []}
    criteria = details.get("criteria", {}).get("child_criteria") or []
    for c in criteria:
        ach = c.get("id")
        if isinstance(ach, dict) and ach.get("id"):
            node["criteria"].append(await build_achievement_subtree(session, region, ach.get("id"), visited, token))
        else:
            # criteria doesn't have linked achievement
            node["criteria"].append({
                "id": c.get("id"),
                "name": c.get("description", "")
            })
    return node

async def get_static_achievement_tree(region):
    # Figure out if we need to refetch index
    now = time.time()
    cache = {}

    if TREE_CACHE_FILE.exists() and TREE_CACHE_FILE.stat().st_size > 0:
        try:
            with open(TREE_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                entry = cache.get(region)
        except Exception as e:
            print("Cache read error:", e)
            cache = {}
        if entry and entry.get("data") and now - entry["timestamp"] < CACHE_TTL:
            print("Loaded achievement tree from cache")
            return entry["data"]

    index = await get_static_achievement_index(region)
    token = fetch_access_token()
    visited = set()
    #results = []
    async with aiohttp.ClientSession() as session:
        results = []
        for i in range(0, len(index), CONCURRENT_LIMIT):
            chunk = index[i:i+CONCURRENT_LIMIT]
            batch = [build_achievement_subtree(session, region, a["id"], visited, token) for a in chunk]
            results.extend(await asyncio.gather(*batch))
    
    cache[region] = {"timestamp": now, "data": results}
    try:
        tmp_file = TREE_CACHE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache, f)
        tmp_file.replace(TREE_CACHE_FILE)
    except Exception as e:
        print("Cache write error:", e)

    return results

async def get_static_achievement_index(region):
    # Figure out if we need to refetch index
    now = time.time()
    cache = {}

    if DROPDOWN_CACHE_FILE.exists() and DROPDOWN_CACHE_FILE.stat().st_size > 0:
        try:
            with open(DROPDOWN_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                entry = cache.get(region)
        except Exception as e:
            print("Cache read error:", e)
            cache = {}
        if entry and entry.get("data") and now - entry["timestamp"] < CACHE_TTL:
            print("Loaded achievements from cache")
            return entry["data"]

    achievements = await fetch_achievement_index(region)
    cache[region] = {"timestamp": now, "data": achievements}
    try:
        tmp_file = DROPDOWN_CACHE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=None)
        tmp_file.replace(DROPDOWN_CACHE_FILE)
    except Exception as e:
        print("Cache write error:", e)
    return achievements