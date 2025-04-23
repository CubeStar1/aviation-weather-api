from shapely.geometry import LineString, Polygon
from location import Location

def path(IDs,Sigco):
    coords=[]
    interrupts={}
    cross=0
    new_coords=[]
    summary=[]
    for sig in Sigco:
        coords.append(sig["coords"])

    for new in coords:
        shapely_coords = [(point['lon'], point['lat']) for point in new]
        new_coords.append(shapely_coords)
  
    for x in range(len(IDs)-1):
        ID1=IDs[x]
        ID2=IDs[x+1]
        loc=Location(ID1)
        coord1=loc[1],loc[0]
        loc=Location(ID2)
        coord2=loc[1],loc[0]
        inter={}
        for sigcoord in new_coords:
            sigmet_polygon = Polygon(sigcoord)

            flight_path = LineString([coord1, coord2])
           
            intersects = flight_path.intersects(sigmet_polygon)
            if intersects == True:
                new
                cross += 1
                inter[cross]=sigmet_polygon
        brief=("Flight between "+ ID1 +" and "+ID2+" encounter(s) " + str(cross)+ " SIGMETS")
        inter["status"]=brief
        summary.append(brief)
        #print(inter)
        cross=0
        interrupts[ID1] = inter
    return interrupts,summary
