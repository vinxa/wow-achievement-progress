# routes.py
import time
import os
from flask import Blueprint, request, jsonify, render_template
from services import realm_api, achievement_api_new
from services.helpers import validate_inputs
from services.rate_limiter import limiter

routes_bp = Blueprint("routes", __name__)
@routes_bp.route("/")
def index():
    return render_template("index.html")

@routes_bp.route("/achievement")
@limiter.limit("30 per minute")
def get_achievement():
    print(request.args)
    character = request.args.get("character")
    server = request.args.get("server")
    ach_id = request.args.get("ach_id")
    region = request.args.get("region", "us")

    if not all([character, server]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
         ach_id = int(ach_id)
         server, character, server_name = validate_inputs(server, character, region)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    result = achievement_api_new.get_achievement_progress(ach_id, region, server, character)
    return jsonify(result)

@routes_bp.route("/realms")
async def get_realms():
    region = request.args.get("region", "us")
    realms = await realm_api.get_realms(region)
    return jsonify(realms)

@routes_bp.route("/status/cache")
def cache_status():
    tree_file = "services/achievement_tree_cache.json"
    drop_file = "services/achievements_cache.json"
    realms_file = "services/realms_cache.json"

    def mod_time(path):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(path))) if os.path.exists(path) else None

    return jsonify({
        "achievement_tree_last_updated": mod_time(tree_file),
        "dropdown_cache_last_updated": mod_time(drop_file),
        "realms_cache_last_updated": mod_time(realms_file)
    })