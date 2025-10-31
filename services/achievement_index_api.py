# services/achievement_index_api.py
import asyncio
import aiohttp
import time
from aiolimiter import AsyncLimiter
from flask import current_app
from models import db, AchievementIndex, AchievementString
from .auth_api import fetch_access_token
from .helpers import region_lookup

CLIENT_TIMEOUT = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
MAX_RETRIES = 5
#RATE_DELAY = 0.2 
RATE_LIMIT = AsyncLimiter(80, 1)

async def throttled_req(session, url, headers):
    # AsyncLimiter here as this controls how fast requests leave the process (how many per second). Delay makes it smooth - forces a delay between starts so they aren't all firing at exactly the same time.
    async with RATE_LIMIT:
        #await asyncio.sleep(RATE_DELAY)
        return await session.get(url, headers=headers)

async def fetch_json(session, url, headers, attempt=1):
        try:
            resp = await asyncio.wait_for(throttled_req(session, url, headers), timeout=30)
            if resp.status == 429:  # Rate limited
                wait = min(2 ** attempt, 10)
                await asyncio.sleep(wait)
                if attempt < MAX_RETRIES:
                    return await fetch_json(session, url, headers, attempt + 1)
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history, status=429, message="Too Many Requests")
            if 400 <= resp.status < 500:
                text = await resp.text()
                raise aiohttp.ClientResponseError(resp.request_info, resp.history, status=resp.status, message=text)
            
            resp.raise_for_status()
            return await resp.json()
        except (aiohttp.ClientOSError, aiohttp.ClientConnectorError, asyncio.TimeoutError, aiohttp.ServerDisconnectedError) as e:
            if attempt < MAX_RETRIES:
                wait = min(2**attempt, 10)
                print(f"[WARN] {e}. retry {attempt}/{MAX_RETRIES} after {wait:.2f}s")
                await asyncio.sleep(wait)
                return await fetch_json(session, url, headers, attempt + 1)
            print(f"[ERROR] {type(e).__name__}: {e} (giving up)")
            raise

async def fetch_achievement_index(region, locale_string=""):
    region = (region or "us").strip().lower()
    if locale_string != "":
        locale_string = f"&locale={locale_string}"
    token = fetch_access_token()
    url = f"https://{region}.api.blizzard.com/data/wow/achievement/index?namespace=static-{region}{locale_string}"
    headers = {"Battlenet-Namespace": f"{region}-static", "Authorization": f"Bearer {token}"}
    print(f"Fetching achievements from {url}...")
    async with aiohttp.ClientSession(timeout=CLIENT_TIMEOUT) as session:
        try:
            result = await fetch_json(session, url, headers)
        except Exception as e:
            print(f"[ERROR] Failed to fetch achievements: {e}")
            return []
    # achievements = []
    return [{"id": a["id"], "name": a["name"]} for a in result.get("achievements", []) if a.get("id") and a.get("name")]

async def fetch_achievement_details(session, ach_id, token):
    region = "us"
    url = f"https://{region}.api.blizzard.com/data/wow/achievement/{ach_id}?namespace=static-{region}"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Fetching achievement {ach_id} details from {url}...")
    try:
        return await fetch_json(session, url, headers)
    except Exception as e:
        print(f"[ERROR] Failed to fetch achievement {ach_id} details: {e}")
        return {"error": f"Failed to fetch {ach_id} details: {e}"}
""" 
async def build_achievement_subtree(session, region, ach_id, visited, token):
    if ach_id in visited:
        return {"id": ach_id, "name": "circular reference safety hit :("}
    visited.add(ach_id)

    details = await fetch_achievement_details(session, region, ach_id, token)
    if not details or "error" in details:
        return {"error": f"Failed to fetch achievement {ach_id} details: {details.get('error')}"}
    
    node = {"id": details.get("id"), "name": details.get("name"), "desc": details.get("description", ""), "criteria": []}
    for c in details.get("criteria", {}).get("child_criteria", []) or []:
        crit_id = c.get("id")
        ach = c.get("achievement")

        if ach and isinstance(ach, dict) and ach.get("id"):
            # recurse into achievement
            subnode = await build_achievement_subtree(session, region, ach["id"], visited, token)
            node["criteria"].append({
                "criteria_id": crit_id,
                "criteria_name": c.get("description", ""),
                "achievement_id": ach["id"],
                "achievement_name": ach.get("name", ""),
                "subtree": subnode,
            })
        else:
            # regular achievement has plain criteria
            node["criteria"].append({
                "criteria_id": crit_id,
                "criteria_name": c.get("description", ""),
            })
    return node """

async def update_db_achievement_index(index, region):
    region_column = region_lookup(region)["db_flag"]
    if not region_column:
        print(f"Unknown region {region}")
        return
    
    with current_app.app_context():
        for a in index:
            ach_id = a.get("id")
            if not ach_id:
                continue
            
            achievement_record = db.session.scalar(
                db.select(AchievementIndex)
                .filter_by(achievement_id=ach_id)
            )
            if not achievement_record:
                achievement_record = AchievementIndex(achievement_id=ach_id)
                details = await fetch_achievement_details(region, ach_id, token)
                
            setattr(achievement_record, region_column, True)

            db.session.add(achievement_record)
        db.session.commit()

async def get_achievement_index(region, locale=None):
    achievements = await fetch_achievement_index(region)
    try:
        await update_db_achievement_index(achievements, region)
    except Exception as e:
        print("Cache write error:", e)
    return achievements

async def get_achievement_details(region, ach_id):
    token = fetch_access_token()
    # Get all achievement IDs
    achievement_records = db.session.scalars(
        db.select(AchievementIndex)
        .filter_by(achievement_id=ach_id)
    ).all()
    if not achievement_records:
        return
    
    # Check if they 
    
    # Check if they have details
    strings_record = db.session.scalar(
        db.select(AchievementString)
        .filter_by(achievement_id=ach_id)
    ).first()
    if not strings_record:
        strings_record = AchievementString(achievement_id=ach_id)
        db.session.add(strings_record)
    details = await fetch_achievement_details(region, ach_id, token)
    strings_record.name = details.get("name", "")
    strings_record.description = details.get("description", "")
    db.session.commit()
    return details
