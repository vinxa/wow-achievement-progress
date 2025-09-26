# app.py
import os
import asyncio
import aiohttp
import time
import json
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone

app = Flask(__name__)

BLIZZ_URL = "https://worldofwarcraft.blizzard.com/en-us/character/us/{server}/{character}/achievement/{ach_id}"

def iso_to_seconds(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return None

async def fetch_achievement(session, ach_id, server, character):
    url = BLIZZ_URL.format(server=server, character=character, ach_id=ach_id)
    print(f"[DEBUG] Fetching {url}")
    try:
        async with session.get(url, timeout=10) as resp:
            text = await resp.text()
            print(f"[DEBUG] Response {resp.status}: {text}")
            resp.raise_for_status()
            return await resp.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch achievement: {e}")
        return {}

async def collect_steps(session, ach_id, server, character, depth=0):
    data = await fetch_achievement(session, ach_id, server, character)
    if not data:
        return []
    data = data.get("achievement", data)

    parent_info = {
        "id": data.get("id", ach_id),
        "done": data.get("completed", False),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "icon": data.get("icon", {}).get("url"),
        "time": iso_to_seconds(data.get("time")) if data.get("time") else None
    }

    steps = []
    tasks = []

    for step in data.get("steps", []):
        node = {
            "id": step.get("id"),
            "done": step.get("completed", False),
            "name": step.get("description", step.get("name", "")),  # treat "description" as the visible name
            "description": "",  # filled in later if this has its own achievement page
            "icon": step.get("icon", {}).get("url"),
            "children": [],
            # "time": iso_to_seconds(data.get("time")) if data.get("time") else None
            "time": None
        }

        if "url" in step:
            sub_id = int(Path(step["url"]).name)

            async def fetch_child(node=node, sub_id=sub_id):
                try:
                    child_data = await fetch_achievement(session, sub_id, server, character)
                    child_data = child_data.get("achievement", child_data)
                    node["description"] = child_data.get("description", "")
                    node["id"] = child_data.get("id", sub_id)
                
                    child_steps, child_info = await collect_steps(session, sub_id, server, character, depth + 1)
                    node["children"] = child_steps
                    node["time"] = child_info.get("time")
                except Exception:
                    node["id"] = sub_id
                    node["description"] = ""

            tasks.append(asyncio.create_task(fetch_child()))

        steps.append(node)

    # progress steps (flat counters)
    for prog in data.get("progressSteps", []):
        steps.append({
            "done": prog.get("completed", False),
            "name": prog.get("description", ""),
            "description": "",
            "count": prog.get("count", 0),
            "total": prog.get("total", 0),
            "children": []
        })

    if tasks:
        await asyncio.gather(*tasks)

    return steps, parent_info


@app.route("/")
def index():
    return render_template("index.html", title="WoW Achievement Progress")

@app.route("/achievement")
def get_achievement():
    character = request.args.get("character")
    server = request.args.get("server")
    ach_id = request.args.get("ach_id")

    if not all([character, server, ach_id]):
        return jsonify({"error": "Missing required fields"}), 400
    
    print(f"[DEBUG] Parsed args: {character} {server} {ach_id}")

    async def build_tree():
        async with aiohttp.ClientSession() as session:
            return await collect_steps(session, int(ach_id), server, character)

    steps, parent_info = asyncio.run(build_tree())

    print(f"[DEBUG] Built tree.")
    return jsonify({
        "ach_id": ach_id,
        "character": character,
        "server": server,
        "parent": parent_info,
        "steps": steps
    })

_realms_cache = {"timestamp": 0, "data": []}
REGION_URLS = {
    "us": "https://worldofwarcraft.blizzard.com/en-us/graphql",
    "eu": "https://worldofwarcraft.blizzard.com/en-gb/graphql",
    "kr": "https://worldofwarcraft.blizzard.com/ko-kr/graphql",
    "tw": "https://worldofwarcraft.blizzard.com/zh-tw/graphql",
}

async def fetch_realms(region="us"):
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

@app.route("/realms")
def get_realms():
    global _realms_cache
    now = time.time()
    region = request.args.get("region", "us")

    if region not in _realms_cache or now - _realms_cache[region]["timestamp"] > 6 * 3600:
        realms = asyncio.run(fetch_realms(region))
        _realms_cache[region] = {"timestamp": now, "data": realms}

    return jsonify(_realms_cache[region]["data"])

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    app.run(debug=debug, use_reloader=False, port=port, host=host)
