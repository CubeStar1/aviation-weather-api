from datetime import datetime, timedelta,timezone
import requests
import json
import re
from avwx import Metar

from UTC import utc



def get_rawM(ID):
    S_ID=ID
    time = utc("Metar")
    url = "https://aviationweather.gov/api/data/metar?ids="+S_ID+"&format=json&taf=true&hours=1&bbox=40%2C-90%2C45%2C-85&date="+time
    req=requests.get(url)
    req=req.json()
    raw=req[0]["rawOb"]
    return raw

def summarise(IDs,metadict):
    for ID in IDs:
        raw = get_rawM(ID)
        parser=Metar(ID)
        Metar.parse(parser,raw)

        summary = parser.summary.split(",")
        summary=summary[0:5]
        summary=', '.join(summary)

        cloud=(parser.translations.clouds)
        remk=parser.translations.remarks
        filt_remk=list({k: v for k, v in remk.items() if not re.fullmatch(r'T\d{8}', k)}.values())

        metadict[ID]={
            "general":summary,
            "cloud": cloud,
            "remarks":filt_remk
        }
    


def summarize_text(data):
    if not data:
        return "No airport data available."

    airports = list(data.items())
    summaries = []

    for i, (code, info) in enumerate(airports):
        is_edge = (i == 0 or i == len(airports) - 1)
        summary = [f"Airport {code}:"]

        if is_edge:
            general_parts = [part.strip() for part in info.get('general', '').split(',')]
            general_map = {}
            for part in general_parts:
                if part.startswith("Winds"):
                    general_map['winds'] = part.replace("Winds", "").strip()
                elif part.startswith("Vis"):
                    general_map['vis'] = part.replace("Vis", "").strip()
                elif part.startswith("Temp"):
                    general_map['temp'] = part.replace("Temp", "").strip()
                elif part.startswith("Dew"):
                    general_map['dew'] = part.replace("Dew", "").strip()
                elif part.startswith("Alt"):
                    general_map['alt'] = part.replace("Alt", "").strip()

            summary.append(
                f"The winds are {general_map.get('winds', 'N/A')}, "
                f"visibility is {general_map.get('vis', 'N/A')}, "
                f"temperature is {general_map.get('temp', 'N/A')}, "
                f"dew point is {general_map.get('dew', 'N/A')}, "
                f"and altimeter setting is {general_map.get('alt', 'N/A')}."
            )

            cloud = info.get('cloud')
            if cloud:
                clean_cloud = cloud.replace(" - Reported AGL", "")
                summary.append(f"Cloud condition: {clean_cloud}.")

            remarks = info.get('remarks', [])
            if remarks:
                summary.append("Remarks: " + "; ".join(remarks) + ".")

        else:
            cloud = info.get('cloud')
            if cloud:
                clean_cloud = cloud.replace(" - Reported AGL", "")
                summary.append(f"Cloud condition: {clean_cloud}.")

        summaries.append("\n".join(summary))

    return "\n\n".join(summaries)

def Metasum(IDs):
    metadict={}
    
    summarise(IDs,metadict)
    summary_text= summarize_text(metadict)
    
    return metadict, summary_text

