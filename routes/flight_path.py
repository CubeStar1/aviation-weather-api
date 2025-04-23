import re
import requests
import json
from flask import jsonify, request
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from shapely.geometry import LineString, Polygon, Point
from shapely.errors import GEOSException
import time

from .metar import get_metar_summary
from .pirep import get_pirep_summary
from .sigmet import get_airsigmet_summary

geolocator = Nominatim(user_agent="aviation-weather-app/1.0")

coordinate_cache = {}

def get_coordinates(identifier):
    """Gets coordinates for an identifier (e.g., airport code) using geopy with caching."""
    if identifier in coordinate_cache:
        return coordinate_cache[identifier]

    try:
        location = geolocator.geocode(f"{identifier} airport", timeout=10)
        if location:
            coords = (location.latitude, location.longitude)
            coordinate_cache[identifier] = coords
            return coords
        else:
            location = geolocator.geocode(identifier, timeout=10)
            if location:
                coords = (location.latitude, location.longitude)
                coordinate_cache[identifier] = coords
                return coords
            else:
                print(f"Warning: Could not geocode identifier: {identifier}")
                coordinate_cache[identifier] = None 
                return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Error geocoding {identifier}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during geocoding for {identifier}: {e}")
        return None

def parse_flight_plan(plan_string):
    """Parses a flight plan string (ID1,ALT1,ID2,ALT2,...) into a list of waypoint dicts."""
    parts = [p.strip() for p in plan_string.split(',')]
    if len(parts) < 2 or len(parts) % 2 != 0:
        raise ValueError("Invalid flight plan format. Expected 'ID1,ALT1,ID2,ALT2,...'")

    waypoints = []
    max_altitude = 0
    for i in range(0, len(parts), 2):
        identifier = parts[i].upper()
        try:
            altitude = int(parts[i+1])
            if altitude > max_altitude:
                max_altitude = altitude
        except ValueError:
            raise ValueError(f"Invalid altitude '{parts[i+1]}' for waypoint {identifier}.")

        coords = get_coordinates(identifier)


        waypoints.append({
            "id": identifier,
            "alt_ft": altitude,
            "coords": coords 
        })

    if len(waypoints) < 2:
        raise ValueError("Flight plan requires at least two valid waypoints with coordinates.")

    return waypoints, max_altitude

def check_sigmet_intersections(leg_start_coords, leg_end_coords, sigmets):
    """Checks if a flight leg intersects with any SIGMET polygons."""
    intersecting_sigmets = []
    if not leg_start_coords or not leg_end_coords:
        return intersecting_sigmets 
    try:
        # Shapely uses (lon, lat)
        flight_leg = LineString([
            (leg_start_coords[1], leg_start_coords[0]),
            (leg_end_coords[1], leg_end_coords[0])
        ])
    except Exception as e:
         print(f"Error creating flight leg LineString: {e}")
         return {"error": "Failed to create flight leg geometry"}


    for sigmet in sigmets:

        if not sigmet or 'area' not in sigmet or not isinstance(sigmet['area'], list):
            continue
        sigmet_coords_list = sigmet['area']
        shapely_coords = [(point.get('lon'), point.get('lat')) for point in sigmet_coords_list if point.get('lon') is not None and point.get('lat') is not None]

        if len(shapely_coords) < 3:
            continue 

        try:
            sigmet_polygon = Polygon(shapely_coords)
            if not sigmet_polygon.is_valid:
                 sigmet_polygon = sigmet_polygon.buffer(0)
                 if not sigmet_polygon.is_valid:
                     print(f"Warning: Invalid SIGMET polygon geometry for {sigmet.get('airSigmetId')}, skipping intersection check.")
                     continue

            if flight_leg.intersects(sigmet_polygon):
                intersecting_sigmets.append({
                    "airSigmetId": sigmet.get('airSigmetId'),
                    "hazard": sigmet.get('hazard'),
                    "severity": sigmet.get('severity'),
                    "simplified_summary": sigmet.get('simplified_summary')
                })

        except (GEOSException, ValueError, TypeError) as e:
            print(f"Error processing SIGMET geometry {sigmet.get('airSigmetId')}: {e}")
        except Exception as e:
            print(f"Unexpected error during intersection check for SIGMET {sigmet.get('airSigmetId')}: {e}")

    return intersecting_sigmets

def get_flight_path_weather(plan_string):
    """Main function to get weather briefing for a flight plan string."""
    results = {
        "flight_plan": plan_string,
        "waypoints": [],
        "legs": [],
        "metar": {},
        "pireps": {},
        "airsigmets": [],
        "errors": [],
        "warnings": []
    }

    try:
        waypoints, max_altitude = parse_flight_plan(plan_string)
        results["waypoints"] = waypoints
    except ValueError as e:
        results["errors"].append(f"Flight Plan Parsing Error: {e}")
        return results 
    except Exception as e:
         results["errors"].append(f"Unexpected Flight Plan Parsing Error: {e}")
         return results

    waypoint_ids = [wp["id"] for wp in waypoints]

    try:
        altitudes_dict = {wp['id']: wp['alt_ft'] for wp in waypoints if wp.get('id') and wp.get('alt_ft') is not None}
        metar_data = get_metar_summary(waypoint_ids, altitudes_dict)
        results["metar"] = metar_data
        for wp_id, data in metar_data.items():
             if data.get("error"):
                 results["warnings"].append(f"METAR fetch/parse failed for {wp_id}: {data['error']}")
    except Exception as e:
        results["errors"].append(f"Failed to fetch METAR data: {e}")

    try:
        pirep_data = get_pirep_summary(waypoint_ids)
        results["pireps"] = pirep_data
        for wp_id, data in pirep_data.items():
             if data.get("error"):
                 results["warnings"].append(f"PIREP fetch/parse failed for {wp_id}: {data['error']}")
    except Exception as e:
        results["errors"].append(f"Failed to fetch PIREP data: {e}")

    try:
        airsigmet_data = get_airsigmet_summary(max_altitude, hazard="ALL")
        if isinstance(airsigmet_data, list):
            results["airsigmets"] = airsigmet_data
        elif isinstance(airsigmet_data, dict) and 'error' in airsigmet_data:
            results["errors"].append(f"Failed to fetch AIRMET/SIGMET data: {airsigmet_data['error']}")
            airsigmet_data = [] 
        else:
             results["warnings"].append("Received unexpected format for AIRMET/SIGMET data.")
             airsigmet_data = []

    except Exception as e:
        results["errors"].append(f"Failed to fetch AIRMET/SIGMET data: {e}")
        airsigmet_data = []

    for i in range(len(waypoints) - 1):
        wp1 = waypoints[i]
        wp2 = waypoints[i+1]
        leg_info = {
            "from": wp1["id"],
            "to": wp2["id"],
            "intersecting_sigmets": []
        }
        if wp1["coords"] and wp2["coords"]:
            intersections = check_sigmet_intersections(wp1["coords"], wp2["coords"], airsigmet_data)
            if isinstance(intersections, dict) and 'error' in intersections:
                 results["warnings"].append(f"SIGMET intersection check failed for leg {wp1['id']}-{wp2['id']}: {intersections['error']}")
            else:
                leg_info["intersecting_sigmets"] = intersections
        else:
            results["warnings"].append(f"Skipping SIGMET intersection check for leg {wp1['id']}-{wp2['id']} due to missing coordinates.")

        results["legs"].append(leg_info)

    for wp in waypoints:
        if wp["coords"] is None:
             results["warnings"].append(f"Could not determine coordinates for waypoint {wp['id']}. Some analysis may be incomplete.")

    return results
