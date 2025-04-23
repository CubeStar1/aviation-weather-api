import requests
import os
import logging
from flask import Blueprint, jsonify
from datetime import datetime, timezone
import math

# --- Blueprint ---
# dashboard_bp = Blueprint('dashboard_bp', __name__) # No longer needed if only used in index.py

# --- Constants & Config ---
OPENWEATHERMAP_API_KEY = "3a7e460c0c8253958ab817ae2d3b97af"

OWM_CURRENT_API_URL = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_API_URL = "https://api.openweathermap.org/data/2.5/forecast" # Added Forecast URL
REQUEST_TIMEOUT = 10

# --- Helper Functions ---
def _format_wind_direction_owm(deg):
    """Converts degrees to cardinal direction."""
    if deg is None: return "N/A"
    try:
        deg = int(deg)
    except (ValueError, TypeError):
        return "N/A"
    val = math.floor((deg / 22.5) + 0.5)
    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return arr[(val % 16)]

def _meters_to_miles(meters):
    """Converts visibility in meters to statute miles."""
    if meters is None: return None
    try:
        miles = float(meters) * 0.000621371
    except (ValueError, TypeError):
        return None
    if miles >= 10: return 10
    if miles >= 1: return round(miles)
    if miles >= 0.75: return 0.75
    if miles >= 0.5: return 0.5
    if miles >= 0.25: return 0.25
    return round(miles, 1)

def _format_forecast_time(unix_timestamp_utc):
    """ Formats UTC timestamp to HH:MM in local time (crude). Warning: Relies on server timezone!"""
    if unix_timestamp_utc is None: return "N/A"
    try:
        # Convert UTC timestamp to datetime object
        dt_utc = datetime.fromtimestamp(unix_timestamp_utc, tz=timezone.utc)
        # Attempt conversion to server's local time - THIS MIGHT NOT BE USER'S LOCAL TIME
        # For more accuracy, timezone info would need to come from client/location
        dt_local = dt_utc.astimezone() 
        return dt_local.strftime("%H:%M")
        # Alternatively, keep it simple with UTC
        # return dt_utc.strftime("%H:%M") + "Z"
    except Exception:
        return "N/A"

# --- Main Function called by the route ---
def get_basic_weather_data(query):
    """Fetches and processes basic weather from OpenWeatherMap for a given query."""
    if not OPENWEATHERMAP_API_KEY:
        logging.error("OpenWeatherMap API key is not set.")
        # Return error object directly
        return {"error": "Server configuration error: Weather API key missing."}, 500

    logging.info(f"Fetching basic weather for query: {query}")
    errors = []
    current_weather_data = None
    forecast_data = None

    params = {
        'q': query,
        'appid': OPENWEATHERMAP_API_KEY,
        'units': 'imperial' 
    }

    # --- Fetch Current Weather ---
    try:
        response = requests.get(OWM_CURRENT_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        current_weather_data = response.json()
        if current_weather_data.get("cod") != 200:
             error_message = current_weather_data.get("message", "Unknown error from OpenWeatherMap Current API")
             logging.warning(f"OpenWeatherMap Current API error for query '{query}': {error_message}")
             errors.append(f"Could not get current weather for '{query}'. {error_message}")
             current_weather_data = None
    except requests.exceptions.HTTPError as e:
         if e.response.status_code == 404:
              logging.warning(f"Location query '{query}' not found by OpenWeatherMap.")
              errors.append(f"Location '{query}' not found for current weather.")
         else:
              logging.error(f"HTTP Error fetching current weather for '{query}': {e}")
              errors.append(f"Current weather service request failed (HTTP {e.response.status_code}).")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Exception fetching current weather for '{query}': {e}")
        errors.append(f"Could not connect to current weather service: {e}")
    except Exception as e:
        logging.error(f"Error processing current weather response for '{query}': {e}")
        errors.append(f"Failed to process current weather response.")

    # --- Fetch Forecast Weather ---
    try:
        response = requests.get(OWM_FORECAST_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        forecast_response = response.json()
        if forecast_response.get("cod") == "200":
             forecast_data = forecast_response.get('list', [])
        else:
            error_message = forecast_response.get("message", "Unknown error from OpenWeatherMap Forecast API")
            logging.warning(f"OpenWeatherMap Forecast API error for query '{query}': {error_message}")
            errors.append(f"Could not get forecast weather for '{query}'. {error_message}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404: # Don't double-log 404 if current failed
             logging.error(f"HTTP Error fetching forecast weather for '{query}': {e}")
             errors.append(f"Forecast weather service request failed (HTTP {e.response.status_code}).")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Exception fetching forecast weather for '{query}': {e}")
        errors.append(f"Could not connect to forecast weather service: {e}")
    except Exception as e:
        logging.error(f"Error processing forecast weather response for '{query}': {e}")
        errors.append(f"Failed to process forecast weather response.")

    # --- Initialize Summary ---
    mapped_summary = {
        "temperature": None, "feelsLike": None, "condition": "Unavailable",
        "windSpeed": None, "windGust": None, "windDirection": "N/A",
        "humidity": None, "pressure": None, "visibility": None,
        "dewPoint": None, "altimeterInHg": None, "ceiling": None,
        "flightCategory": None, "heatIndex": None, "warnings": [], 
        "hourlyForecast": [],
    }

    # --- Map Current Data (if available) ---
    if current_weather_data:
        main = current_weather_data.get('main', {})
        wind = current_weather_data.get('wind', {})
        weather_desc = current_weather_data.get('weather', [{}])[0]
        visibility_meters = current_weather_data.get('visibility')
        wind_speed_mph = wind.get('speed')
        wind_gust_mph = wind.get('gust')
        location_name = current_weather_data.get('name')

        mapped_summary.update({
            "name": location_name,
            "temperature": round(main.get('temp')) if main.get('temp') is not None else None,
            "feelsLike": round(main.get('feels_like')) if main.get('feels_like') is not None else None,
            "condition": weather_desc.get('description', 'Unknown').capitalize(),
            "windSpeed": round(wind_speed_mph) if wind_speed_mph is not None else None,
            "windGust": round(wind_gust_mph) if wind_gust_mph is not None else None,
            "windDirection": _format_wind_direction_owm(wind.get('deg')),
            "humidity": main.get('humidity'),
            "pressure": main.get('pressure'),
            "visibility": _meters_to_miles(visibility_meters),
        })

    # --- Map Forecast Data (if available) ---
    if forecast_data:
        hourly_forecast = []
        for forecast_entry in forecast_data[:8]: # Get ~24 hours
            dt = forecast_entry.get('dt')
            temp = forecast_entry.get('main', {}).get('temp')
            condition_desc = forecast_entry.get('weather', [{}])[0].get('main', 'Unknown')
            
            if dt is not None and temp is not None:
                 hourly_forecast.append({
                     "time": _format_forecast_time(dt),
                     "condition": condition_desc, 
                     "temp": round(temp) 
                 })
        mapped_summary["hourlyForecast"] = hourly_forecast
    
    # --- Determine Status Code ---
    status_code = 200
    if errors and not current_weather_data and not forecast_data:
         status_code = 503 # Failed to get any data
    elif errors:
         status_code = 207 # Got partial data

    # --- Construct Final Response Object ---
    final_response = {
        **mapped_summary,
        "query": query,
        "lastUpdatedUTC": datetime.utcnow().strftime("%H:%M UTC"),
        "errors": errors
    }

    # --- Return the final response object and status code ---
    return final_response, status_code

# Removed the jsonify wrapper function `get_basic_weather` as it's handled in index.py


