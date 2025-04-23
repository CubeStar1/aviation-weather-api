from datetime import datetime, timedelta,timezone

def utc(type):
    if type == "Metar":
        one_hour_back = datetime.now(timezone.utc) - timedelta(hours=1)
        adjusted_time = one_hour_back.replace(minute=54, second=0, microsecond=0)
        formatted_time = adjusted_time.strftime("%Y%m%d_%H%M%SZ")
        return (formatted_time)

    elif type == "Sigmet":  
        time=(datetime.now(timezone.utc))
        formatted_time = time.strftime("%Y%m%d_%H%M%SZ")
        return (formatted_time)


