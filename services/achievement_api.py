# app/services/achievement_api.py

import asyncio
import aiohttp
import re
from datetime import datetime
from pathlib import Path

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
        return {"error": f"Failed to fetch achievement {ach_id}: {e}"}

async def collect_steps(session, ach_id, server, character, depth=0):
    data = await fetch_achievement(session, ach_id, server, character)
    if "error" in data:
        return {"error": data["error"]}, {}

    if not data:
        return [], {}
    
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


def sanitize_slug(text: str) -> str:
    return re.sub(r'[^A-Za-z0-9-]', '', text)

def get_achievement_progress(ach_id, server, character):
    async def build_tree():
        async with aiohttp.ClientSession() as session:
            return await collect_steps(session, int(ach_id), sanitize_slug(server), character)
         
    print(f"[DEBUG] Built tree.")
    return asyncio.run(build_tree())




