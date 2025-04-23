import requests
import json
from flask import jsonify
import logging

from ..utils import get_utc_time_for_api

logger = logging.getLogger(__name__)



def get_airsigmet_summary(altitude_ft, hazard="ALL"):
    """
    Fetches AIRMET/SIGMET data based on altitude and hazard type.

    Args:
        altitude_ft (int): Altitude in feet.
        hazard (str): Hazard type (e.g., 'CONV', 'TURB', 'ICE', 'IFR', 'ALL'). Defaults to 'ALL'.

    Returns:
        list: A list of dictionaries, each representing an AIRMET/SIGMET report.
              Returns an empty list if no reports are found or an error occurs.
    """
    try:
        altitude_param = int(altitude_ft) # Ensure altitude is integer
    except (ValueError, TypeError):
        print(f"Error: Invalid altitude provided: {altitude_ft}")
        return {"error": "Invalid altitude format. Must be an integer."}

    time_str = get_utc_time_for_api("Sigmet")

    level_param = altitude_param // 100

    valid_hazards = ["CONV", "TURB", "ICE", "IFR", "MTN OBSCN", "ALL"]
    if hazard.upper() not in valid_hazards:
         print(f"Warning: Invalid hazard type '{hazard}'. Defaulting to 'ALL'.")
         hazard = "ALL"

    url = f"https://aviationweather.gov/api/data/airsigmet?format=json&level={level_param}&hazard={hazard.upper()}&date={time_str}"

    try:
        logger.info(f"Fetching AIRSIGMET: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Received {len(data)} AIRSIGMET reports from API.")
        processed_data = []
        for report in data:
            try:
                report["simplified_summary"] = generate_summary_string(report)
                processed_data.append(report)
            except Exception as e_gen:
                 logger.error(f"Error generating summary for AIRSIGMET {report.get('airSigmetId', 'N/A')}: {e_gen}", exc_info=True)
                 processed_data.append(report) 

        logger.info(f"Returning {len(processed_data)} processed AIRSIGMET reports.")
        return processed_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching AIRSIGMET data: {e}")
        return {"error": f"Failed to fetch AIRSIGMET data: {e}"}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response for AIRSIGMET: {e}")
        return {"error": "Failed to decode AIRSIGMET response"}
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_airsigmet_summary: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {e}"}

def generate_summary_string(report):
    """Helper function to create a summary string from a report dictionary."""
    try:
        hazard = report.get('hazard', 'Unknown Hazard')
        severity = report.get('severity', 'unknown severity')
        alt_hi = report.get('altitudeHi1')
        alt_lo = report.get('altitudeLo1')

        if alt_hi is not None:
            level_str = f"up to FL{alt_hi // 100}"
        elif alt_lo is not None:
             level_str = f"at FL{alt_lo // 100}"
        else:
            level_str = "at unknown altitude"

        mov_dir = report.get('movementDir')
        mov_spd = report.get('movementSpd')

        summary = f"{hazard} ({severity}) {level_str}."
        if mov_dir is not None and mov_spd is not None:
            summary += f" Moving {mov_dir}° at {mov_spd} kt."

        return summary
    except Exception as e:
        print(f"Error generating summary string for report {report.get('airSigmetId', '')}: {e}")
        return "Error generating summary."

