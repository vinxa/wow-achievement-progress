# routes.py
from flask import Blueprint, request, jsonify, render_template
from services import achievement_api, realm_api, achievement_index_api, achievement_api_new
from services.helpers import validate_inputs
from services.rate_limiter import limiter

routes_bp = Blueprint("routes", __name__)
@routes_bp.route("/")
def index():
    return render_template("index.html")

@routes_bp.route("/achievement")
@limiter.limit("5 per minute")
def get_achievement():
    print(request.args)
    character = request.args.get("character")
    server = request.args.get("server")
    # ach_id = request.args.get("ach_id")
    region = request.args.get("region", "us")

    if not all([character, server]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
         server, character, server_name = validate_inputs(server, character, region)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    result = achievement_api_new.get_character_achievements(region, server, character)
    #get_achievement_progress(ach_id, region, server, character, cache)
    return jsonify(result)

@routes_bp.route("/realms")
def get_realms():
    region = request.args.get("region", "us")
    realms = realm_api.get_realms(region)
    return jsonify(realms)

@routes_bp.route("/achievements")
def get_achievements():
    query = request.args.get("q")
    region = request.args.get("region", "us")
    if query:
        return jsonify(achievement_index_api.search_achievements(query, region))
    else:
        return jsonify(achievement_index_api.get_static_achievement_index(region))
    