# app/services/realm_api.py

import aiohttp
import asyncio
import time

REGION_URLS = {
    "us": "https://worldofwarcraft.blizzard.com/en-us/graphql",
    "eu": "https://worldofwarcraft.blizzard.com/en-gb/graphql",
    "kr": "https://worldofwarcraft.blizzard.com/ko-kr/graphql",
    "tw": "https://worldofwarcraft.blizzard.com/zh-tw/graphql",
}
_realms_cache = {"timestamp": 0, "data": []}

async def fetch_realms(region):
    url = REGION_URLS.get(region, REGION_URLS["us"])
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


def get_realms(region):
    now = time.time()
    if region not in _realms_cache or now - _realms_cache[region]["timestamp"] > 6 * 3600:
        realms = asyncio.run(fetch_realms(region))
        _realms_cache[region] = {"timestamp": now, "data": realms}

    return _realms_cache[region]["data"]