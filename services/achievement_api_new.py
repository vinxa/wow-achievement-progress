# app/services/achievement_api.py

import asyncio
import aiohttp
import time
from flask import current_app
from .helpers import sanitize_slug
from .auth_api import fetch_access_token

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
                "n": c.get("description", ""),
                "c": c.get("is_completed", False),
                "count": c.get("quantity", 0),
                "total": c.get("max_quantity", 0),
                "amount": c.get("amount", 0),
                "criteria": parse_criteria(c.get("child_criteria")),
            }
            children.append(node)
        return children

    parsed = []
    for ach in data.get("achievements", []):
        ach_obj = ach.get("achievement", {})
        current_app.logger.info(ach)
        node = {
            "id": ach_obj.get("id"),
            "n": ach_obj.get("name"),
            "desc" : ach_obj.get("description", ""),
            "c": ach.get("is_completed", False)
            or bool(ach.get("completed_timestamp")),
            "t": ach.get("completed_timestamp"),
            "criteria": parse_criteria(ach.get("criteria", {}).get("child_criteria")),
        }
        current_app.logger.info(node)
        
        parsed.append(node)
    return parsed

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
    achievements = asyncio.run(fetch_character_achievements(region, sanitize_slug(server), character))
    node = find_achievement_helper(ach_id, achievements)
    if not node:
        return {"error": f"Achievement {ach_id} not found..."}
    progress = []
    if "criteria" in node:
        for c in node["criteria"] or []:
            progress.append({
                "id": c["id"],
                "n": c["n"],
                "c": c["c"],
                "count": c.get("count", 0),
                "total": c.get("total", 0),
            })

    return {
        "id": node.get("id"),
        "n": node.get("n"),
        "desc": node.get("desc"),
        "c": node.get("c", False),
        "t": node.get("t"),
        "progress": progress,
    }
