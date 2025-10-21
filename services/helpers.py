import re
import asyncio
from datetime import datetime
from .realm_api import get_realms
from .achievement_index_api import get_static_achievement_tree

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

async def refresh_server_caches():
    print("[SCHEDULER] Cache refresh starting...")
    print("[SCHEDULER] Refreshing realms...")
    regions = ["us", "eu", "kr", "tw"]
    try:
        for region in regions:
            await get_realms(region)
    except Exception as e:
        print(f"[SCHEDULER] Realm refresh failed: {e}")

    print("[SCHEDULER] Refreshing achievements...")
    try:
        for region in regions:
            await get_static_achievement_tree(region)
    except Exception as e:
        print(f"[SCHEDULER] Cache refresh failed: {e}")
    print("[SCHEDULER] Cache refresh complete.")