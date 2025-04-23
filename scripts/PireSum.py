from avwx import Pireps
from collections import defaultdict
import requests
from UTC import utc

def Piresum(IDs):
    summary=[]
    raw={}
    for ID in IDs:
        new=Pireps(ID)
        pireps={}
        time=utc("Metar")
        counters = defaultdict(int)
        x="https://aviationweather.gov/api/data/pirep?id="+ID+"&format=raw&age=1&distance=1000&level=10000&inten=sev&date="+time
        req=requests.get(x)
        pirep_lines = req.text.strip().split('\n')
        counter=0
        for line in pirep_lines:
            if "TOP" in line and "T" in line:  # crude filter
                continue
            Pireps.parse(new,line)
            data=new.data
            counter += 1
            pireps[counter]=data
         
            if data == None:
                pass
            else:
                for pirep in data:
                    if pirep.clouds is not None:
                        counters['clouds'] += 1
                    if pirep.flight_visibility is not None:
                        counters['flight_visibility'] += 1
                    if pirep.icing is not None:
                        counters['icing'] += 1
                    if pirep.turbulence is not None:
                        counters['turbulence'] += 1

            

        counters=dict(counters)
        
        output = f"{ID}: " + ", ".join(f"{k}={v}" for k, v in counters.items())
        summary.append(output)
        pireps["status"]=output
        raw[ID]=pireps
    summary="\n\n".join(summary)
    return raw,summary

