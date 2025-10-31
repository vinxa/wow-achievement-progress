import re
from datetime import datetime

def validate_inputs(server, character, region):
    from .realm_api import get_realms
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

async def refresh_achievement_data():
    from app import create_app
    app = create_app()
    from .realm_api import get_realms
    from .achievement_index_api import get_achievement_index
    with app.app_context():
        print("[SCHEDULER] Achievement db refresh starting...")
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
                await get_achievement_index(region)
        except Exception as e:
            print(f"[SCHEDULER] Achievement db refresh failed: {e}")
    print("[SCHEDULER] Achievement db refresh complete.")

def region_lookup(region):
    data = {
        "us": {"graphql_url": "https://worldofwarcraft.blizzard.com/en-us/graphql", 
               "locales": ["en_US","es_MX", "pt_BR"], "db_flag": "exists_us"},
        "eu": {"graphql_url": "https://worldofwarcraft.blizzard.com/en-gb/graphql", 
               "locales": ["en_GB", "es_ES", "fr_FR", "ru_RU", "de_DE", "pt_PT", "it_IT"], "db_flag": "exists_eu"},
        "kr": {"graphql_url": "https://worldofwarcraft.blizzard.com/ko-kr/graphql", 
               "locales": ["ko_KR"], "db_flag": "exists_kr"},
        "tw": {"graphql_url": "https://worldofwarcraft.blizzard.com/zh-tw/graphql", 
               "locales": ["zh_TW"], "db_flag": "exists_tw"},
    }
    region = (region or "us").strip().lower()
    return data.get(region, data["us"])