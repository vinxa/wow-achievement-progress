# app/services/achievement_api.py

import asyncio
import aiohttp
import time
from .helpers import (
    iso_to_seconds,
    sanitize_slug,
    fetch_access_token
)
CACHE_TTL = 15 * 60  # Caches character data for 15 minutes

async def fetch_character_achievements(region, realm, character):
    token = fetch_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "namespace": f"profile-{region.lower()}",
        "locale": "en_US",
    }
    url = (
        f"https://{region.lower()}.api.blizzard.com/profile/wow/character/"
        f"{realm.lower()}/{character.lower()}/achievements"
    )
    print(f"Fetching achievements from {url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                resp.raise_for_status()
                result = await resp.json()
        return parse_character_achievements(result)
    except Exception as e:
        print(f"[ERROR] Failed to fetch achievements: {e}")
        return {"error": f"Failed to fetch achievements: {e}"}

def parse_character_achievements(data):
    def parse_criteria(criteria_list):
        children = []
        for c in criteria_list or []:
            node = {
                "id": c.get("id"),
                "name": c.get("description", ""),
                "done": c.get("is_completed", False),
                "count": c.get("quantity", 0),
                "total": c.get("max_quantity", 0),
                "children": parse_criteria(c.get("child_criteria")),
            }
            children.append(node)
        return children

    parsed = []
    for ach in data.get("achievements", []):
        ach_obj = ach.get("achievement", {})
        node = {
            "id": ach_obj.get("id"),
            "name": ach_obj.get("name"),
            "description": ach_obj.get("description"),
            "done": ach.get("completed", False)
            or bool(ach.get("completed_timestamp")),
            "time": ach.get("completed_timestamp"),
            "criteria": parse_criteria(ach.get("criteria", {}).get("child_criteria")),
        }
        parsed.append(node)
    return parsed

def get_character_achievements(region, realm, character):
    data = asyncio.run(fetch_character_achievements(region, realm, character))
    return data

def find_achievement_helper(target_id, achievements):
    def find_in_criteria(criteria_list):
        for c in criteria_list or []:
            if c["id"] == target_id:
                return c
            found = find_in_criteria(c.get("children"))
            if found:
                return found
        return None

    for ach in achievements:
        if ach["id"] == target_id:
            return ach
        found = find_in_criteria(ach.get("criteria"))
        if found:
            return found
    return None

def get_achievement_progress(ach_id, region, server, character):
    try:
        ach_id = int(ach_id)
    except ValueError:
        return {"error": "Invalid achievement id"}
    
    achievements = get_character_achievements(region, sanitize_slug(server), character)
    node = find_achievement_helper(ach_id, achievements)
    if not node:
        return {"error": f"Achievement {ach_id} not found..."}
    
    if "criteria" in node:
        progress = []
        for c in node["criteria"] or []:
            progress.append({
                "id": c["id"],
                "name": c["name"],
                "done": c["done"],
                "count": c.get("count", 0),
                "total": c.get("total", 0),
            })
    else:
        progress = []

    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "description": node.get("description"),
        "done": node.get("done", False),
        "time": node.get("time"),
        "progress": progress,
    }




