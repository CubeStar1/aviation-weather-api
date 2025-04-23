from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="SongBird") 

def get_airport_coordinates(airport_name):

    location = geolocator.geocode(airport_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        return None

def Location(ID):
    
    airport_name1 = ID
    coordinates = get_airport_coordinates(airport_name1)

    if coordinates:
        return coordinates
    else:
        print(f"Could not find coordinates")
