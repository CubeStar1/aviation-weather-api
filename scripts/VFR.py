
def extract_visibility_and_cloud(data):
    results = {}
    for icao, info in data.items():
        general = info.get("general", "")
        cloud = info.get("cloud", "")

        # Extract visibility
        visibility = None
        for part in general.split(','):
            if "Vis" in part:
                try:
                    visibility = float(part.split("Vis")[1].strip().replace("sm", ""))
                except ValueError:
                    visibility = None

        # Clean cloud description
        cloud_clean = cloud.replace(" - Reported AGL", "")

        results[icao] = {
            "visibility_sm": visibility,
            "cloud_cover": cloud_clean
        }

    return results

# Sample dictionary


def is_vfr_allowed(visibility, cloud_cover, altitude):
    if visibility < 3.0:
        return False
    if altitude > 18000:
        return False
    if "sky clear" in cloud_cover.lower():
        return True

    import re
    cloud_layers = re.findall(r'at (\d+)ft', cloud_cover)
    cloud_bases = [int(height) for height in cloud_layers]

    for base in cloud_bases:
        if altitude > base - 1000:
            return False
    altitude=int(altitude)
    
    return True



# Evaluate each airport



def vfr(airport_data,altitudes):
    cloudvis = extract_visibility_and_cloud(airport_data)
    vfr_results = {}
    for airport, data in cloudvis.items():
        vis = data['visibility_sm']
        cloud = data['cloud_cover']
        alt = altitudes[airport]

        vfr_results[airport] = is_vfr_allowed(vis, cloud, alt)


    for airport, allowed in vfr_results.items():
        status = "VFR Allowed" if allowed else "VFR Not Allowed"
        print(f"{airport}: {status}")




