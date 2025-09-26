import re
from .realm_api import get_realms
from datetime import datetime


def validate_inputs(server, character, ach_id, region):
    realms = get_realms(region)

    server_obj = next(
        (r for r in realms if r["slug"].lower() == server.lower() or r["name"].lower() == server.lower()),
        None
    )
    if not server_obj:
        raise ValueError(f"Invalid server: {server}")

    return int(ach_id), server_obj["slug"], character, server_obj["name"]


def sanitize_slug(text: str) -> str:
    return re.sub(r'[^A-Za-z0-9-]', '', text)


def iso_to_seconds(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return None