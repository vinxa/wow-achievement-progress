# routes.py
from flask import Blueprint, request, jsonify, render_template
from services import achievement_api, realm_api
from services import achievement_api
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
    ach_id = request.args.get("ach_id")
    region = request.args.get("region", "us")

    if not all([character, server, ach_id]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        ach_id, server, character, server_name = validate_inputs(server, character, ach_id, region)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    steps, parent_info = achievement_api.get_achievement_progress(
        int(ach_id), server, character)

    if isinstance(steps, dict) and "error" in steps:
        return jsonify(steps), 404

    return jsonify({
        "ach_id": ach_id,
        "character": character,
        "server": server,
        "server_name": server_name,
        "parent": parent_info,
        "steps": steps
    })

@routes_bp.route("/realms")
def get_realms():
    region = request.args.get("region", "us")
    realms = realm_api.get_realms(region)
    return jsonify(realms)
