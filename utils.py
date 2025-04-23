from datetime import datetime, timedelta, timezone

def get_utc_time_for_api(report_type):
    """
    Generates a UTC timestamp string formatted for the aviationweather.gov API,
    matching the logic from the original UTC.py script.

    Args:
        report_type (str): The type of report ('Metar', 'Sigmet', etc.) 
                           to determine specific time adjustments if needed.

    Returns:
        str: Formatted UTC timestamp string (e.g., YYYYMMDD_HHMMZ).
    """
    now_utc = datetime.now(timezone.utc)
    
    if report_type.lower() == "metar":
        adjusted_time = (now_utc - timedelta(hours=1)).replace(minute=54, second=0, microsecond=0)
        formatted_time = adjusted_time.strftime("%Y%m%d_%H%M") + "Z"
        return formatted_time
    elif report_type.lower() == "sigmet":  
        formatted_time = now_utc.strftime("%Y%m%d_%H%M") + "Z"
        return formatted_time
    else:
        formatted_time = now_utc.strftime("%Y%m%d_%H%M") + "Z"
        return formatted_time

