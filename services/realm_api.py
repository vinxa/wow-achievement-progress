# app/services/realm_api.py

import aiohttp
import asyncio
import time
import json
from pathlib import Path
from .helpers import region_lookup

CACHE_FILE = Path(__file__).parent / "realms_cache.json"
CACHE_TTL = 24 * 3600  # 1 day
_realms_cache: dict[str, dict] = {}

async def fetch_realms(region):
    url = region_lookup(region).get("graphql_url")

    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

    # first try: persisted query only
    body_hash = {
        "operationName": "GetRealmStatusData",
        "variables": {"input": {"compoundRegionGameVersionSlug": region}},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "b37e546366a58e211e922b8c96cd1ff74249f564a49029cc9737fef3300ff175"
            }
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=body_hash) as resp:
            text = await resp.text()
            print("=== [persisted‐only] status:", resp.status)
            print(text[:1000])
            try:
                data = await resp.json()
            except Exception as e:
                data = {}
                print("Failed to parse JSON from hash request:", e)

    # check if data has realms
    items = data.get("data", {}).get("Realms", [])
    if not items:
        # fallback: send full query
        full_query = """
        query GetRealmStatusData($input: RealmStatusInput) {
          Realms(input: $input) {
            name
            slug
            timezone
            online
            population {
              name
            }
            type {
              name
            }
          }
        }
        """
        body_full = {
            "operationName": "GetRealmStatusData",
            "variables": {"input": {"compoundRegionGameVersionSlug": region}},
            "query": full_query
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body_full) as resp2:
                text2 = await resp2.text()
                print("=== [fallback full] status:", resp2.status)
                print(text2[:1000])
                try:
                    data = await resp2.json()
                except Exception as e:
                    print("Failed to parse fallback JSON:", e)
                    data = {}

    realms = []
    for r in data.get("data", {}).get("Realms", []):
        realms.append({
            "name": r.get("name"),
            "slug": r.get("slug"),
            "timezone": r.get("timezone"),
            "online": r.get("online"),
            "population": r.get("population", {}).get("name"),
            "type": r.get("type", {}).get("name"),
            "region": region
        })
    return realms


async def get_realms(region):
    now = time.time()
    cache = {}

    # Try loading cache file safely
    if CACHE_FILE.exists() and CACHE_FILE.stat().st_size > 0:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception as e: # corrupted cache
            print("Cache read error:", e)
            cache = {}

    entry = cache.get(region)
    if entry and now - entry["timestamp"] < CACHE_TTL:
        print("Loaded realms from cache")
        return entry["data"]

    # cache expired or missing
    print("Fetching realms from blizzard...")
    realms = await fetch_realms(region)

    # update memory cache
    cache[region] = {"timestamp": now, "data": realms}

    # save back to cache
    try:
        tmp_file = CACHE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache, f)
        tmp_file.replace(CACHE_FILE)
    except Exception as e:
        print("Failed to write cache:", e)

    return realms