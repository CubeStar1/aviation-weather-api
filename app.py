from flask import Flask, jsonify, request
from flask_cors import CORS # Import CORS

# Import functions from the routes modules
# Using absolute import from the 'api' package perspective
# This assumes the Flask app is run with the parent directory in PYTHONPATH
# or using 'flask run' from the parent directory after setting FLASK_APP=api.index
try:
    from api.routes.metar import get_metar_summary
    from api.routes.pirep import get_pirep_summary
    from api.routes.sigmet import get_airsigmet_summary
    from api.routes.flight_path import get_flight_path_weather
    from api.routes.dashboard import get_basic_weather_data
    from api.routes.ai_summary import configure_gemini, generate_weather_summary
except ImportError:
    print("Attempting relative imports for routes...")
    from routes.metar import get_metar_summary
    from routes.pirep import get_pirep_summary
    from routes.sigmet import get_airsigmet_summary
    from routes.flight_path import get_flight_path_weather
    from routes.dashboard import get_basic_weather_data
    from routes.ai_summary import configure_gemini, generate_weather_summary

import os

app = Flask(__name__)
CORS(app) 

GEMINI_API_KEY = "AIzaSyAoiHl2F6SMyinRe6pwrBbBl-6L22pexe0"
if GEMINI_API_KEY:
    configure_gemini(GEMINI_API_KEY)

@app.route("/api/metar", methods=['POST'])
def metar_route():
    """Endpoint to get METAR summary for a list of airport IDs."""
    data = request.get_json()
    if not data or 'ids' not in data or not isinstance(data['ids'], list):
        return jsonify({"error": "Invalid request. Body must be JSON with an 'ids' list."}), 400
    
    airport_ids = data['ids']
    altitudes = data.get('altitudes') 
    
    if altitudes is not None:
        if not isinstance(altitudes, dict):
             return jsonify({"error": "Invalid request. 'altitudes' must be an object/dictionary."}), 400
        

    try:
        metar_data = get_metar_summary(airport_ids, altitudes)
        return jsonify(metar_data)
    except Exception as e:
        print(f"Error in /api/metar route: {e}")
        return jsonify({"error": "An internal error occurred processing METAR request."}), 500

@app.route("/api/pirep", methods=['POST'])
def pirep_route():
    """Endpoint to get PIREP summary for a list of location IDs."""
    data = request.get_json()
    if not data or 'ids' not in data or not isinstance(data['ids'], list):
        return jsonify({"error": "Invalid request. Body must be JSON with an 'ids' list."}), 400
    
    location_ids = data['ids']
    try:
        pirep_data = get_pirep_summary(location_ids)
        return jsonify(pirep_data)
    except Exception as e:
        print(f"Error in /api/pirep route: {e}")
        return jsonify({"error": "An internal error occurred processing PIREP request."}), 500

@app.route("/api/airsigmet", methods=['GET'])
def airsigmet_route():
    """Endpoint to get AIRMET/SIGMET data based on altitude and optional hazard."""
    altitude = request.args.get('altitude')
    hazard = request.args.get('hazard', default="ALL", type=str)

    if altitude is None:
        return jsonify({"error": "Missing required query parameter: altitude (in feet)"}), 400

    try:
        altitude_ft = int(altitude)
    except ValueError:
         return jsonify({"error": "Invalid altitude format. Must be an integer."}), 400

    try:
        airsigmet_data = get_airsigmet_summary(altitude_ft, hazard)
        return jsonify(airsigmet_data)
    except Exception as e:
        print(f"Error in /api/airsigmet route: {e}")
        return jsonify({"error": "An internal error occurred processing AIRMET/SIGMET request."}), 500

@app.route("/api/flight_briefing", methods=['POST'])
def flight_briefing_route():
    """Endpoint to get a comprehensive weather briefing for a flight plan."""
    data = request.get_json()
    if not data or 'plan' not in data:
        return jsonify({"error": "Invalid request. Body must be JSON with a 'plan' string."}), 400

    plan_string = data['plan']
    if not isinstance(plan_string, str) or not plan_string:
         return jsonify({"error": "Invalid 'plan' format. Must be a non-empty string."}), 400

    try:
        briefing_data = get_flight_path_weather(plan_string)
        
        if briefing_data.get("errors"):
            return jsonify(briefing_data), 400
            
        return jsonify(briefing_data)
        
    except Exception as e:
        print(f"Error in /api/flight_briefing route: {e}")
        return jsonify({"error": "An internal error occurred processing flight briefing request."}), 500

@app.route("/api/weather_summary", methods=['POST'])
def weather_summary_route():
    """Endpoint to get an AI-generated weather summary for a flight briefing."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request. Body must be JSON with briefing data."}), 400

    try:
        if not GEMINI_API_KEY:
            return jsonify({"error": "AI summary not available - Gemini API key not configured"}), 503
            
        ai_summary = generate_weather_summary(data)
        return jsonify({"summary": ai_summary})
        
    except Exception as e:
        print(f"Error in /api/weather_summary route: {e}")
        return jsonify({"error": "An internal error occurred generating weather summary."}), 500

@app.route('/api/basic_weather/<string:query>', methods=['GET'])
def basic_weather_route(query):
    """Endpoint to get basic weather summary for a location query."""
    try:
        weather_data, status_code = get_basic_weather_data(query)
        return jsonify(weather_data), status_code
    except Exception as e:
        print(f"Error in /api/basic_weather route: {e}") 
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route("/")
def index():
    return jsonify({"message": "Aviation Weather API is running."}) 
