import requests
import json
from avwx import AirSigmet

from UTC import utc

def Sigmetsum(alti):  
    alti=str(alti)
    hazs="conv"
    time = utc("Sigmet")
    url="https://aviationweather.gov/api/data/airsigmet?format=json&hazard="+hazs+"&level="+alti+"&date="+time
    req=requests.get(url)
    req=req.json()
    sigmets=[]
    for sigmet in req:
    
        flight_level = sigmet['altitudeHi1'] // 100 if sigmet['altitudeHi1'] else 'unknown'

        summary = (
            f"{sigmet['hazard']} SIGMET of severity {sigmet['severity']} "
            f"at Flight Level FL{flight_level}, moving towards {sigmet['movementDir']}° "
            f"at speed {sigmet['movementSpd']} kt."
        )
        if sigmet["movementDir"] == None or sigmet['movementSpd'] == None:
            pass
        else:
            sigmets.append(summary)
    return req,sigmets
   

