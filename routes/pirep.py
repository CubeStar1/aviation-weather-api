import requests
from avwx import Pireps
from collections import defaultdict
import json

# Import the utility function
from ..utils import get_utc_time_for_api


def get_pirep_summary(location_ids):
    """
    Fetches and summarizes PIREP data near a list of location IDs.
    Returns a dictionary with location IDs as keys and their PIREP data.
    """
    pirep_data = {}
    if not isinstance(location_ids, list):
        raise TypeError("location_ids must be a list")

    for location_id in location_ids:
        pireps_for_location = {}
        summary_counters = defaultdict(int)

        url = f"https://aviationweather.gov/api/data/pirep?id={location_id}&format=raw&age=1&distance=100"


        try:
            response = requests.get(url)
            response.raise_for_status()
            raw_pirep_text = response.text.strip()

            if not raw_pirep_text or "No PIREPs" in raw_pirep_text:
                 pireps_for_location["status"] = f"{location_id}: No recent PIREPs found within parameters."
                 pireps_for_location["reports"] = []

            else:
                pirep_lines = raw_pirep_text.split('\n')
                parsed_reports = []
                report_counter = 0
                parser = Pireps(location_id) 
                for line in pirep_lines:
                    if "TOP" in line and "T" in line:
                        continue
                    if parser.parse(line):
                        if parser.data:
                            report_counter += 1
                            parsed_report_data = parser.data[0].__dict__ 
                            parsed_reports.append(parsed_report_data)

                            if parsed_report_data.get('clouds') is not None:
                                summary_counters['clouds'] += 1
                            if parsed_report_data.get('flight_visibility') is not None:
                                summary_counters['flight_visibility'] += 1
                            if parsed_report_data.get('icing') is not None:
                                summary_counters['icing'] += 1
                            if parsed_report_data.get('turbulence') is not None:
                                summary_counters['turbulence'] += 1
                        else:
                             print(f"Warning: PIREP parser succeeded but produced no data for line: {line}")


                if summary_counters:
                     summary_str = f"{location_id}: Reports found with " + ", ".join(f"{k}={v}" for k, v in summary_counters.items())
                else:
                     summary_str = f"{location_id}: Parsed {report_counter} PIREP(s), no specific conditions counted."

                pireps_for_location["status"] = summary_str
                pireps_for_location["reports"] = parsed_reports 

        except requests.exceptions.RequestException as e:
            print(f"Error fetching PIREPs for {location_id}: {e}")
            pireps_for_location["status"] = f"{location_id}: Error fetching data."
            pireps_for_location["reports"] = []
            pireps_for_location["error"] = str(e)
        except Exception as e:
             print(f"Error processing PIREPs for {location_id}: {e}")
             pireps_for_location["status"] = f"{location_id}: Error processing data."
             pireps_for_location["reports"] = []
             pireps_for_location["error"] = str(e)


        pirep_data[location_id] = pireps_for_location

    return pirep_data
