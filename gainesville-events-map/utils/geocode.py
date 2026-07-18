from geopy.geocoders import Nominatim
import pandas as pd
import time
import os

# Predefined locations for major Gainesville spots to ensure reliable geocoding
# and to prevent offline/rate-limiting errors during tests/deployment.
PREDEFINED_COORDINATES = {
    "visit gainesville": (29.6519, -82.3248),
    "alachua county library district": (29.6515, -82.3244),
    "cade museum": (29.6443, -82.3168),
    "florida museum of natural history": (29.6381, -82.3692),
    "harn museum of art": (29.6370, -82.3698),
    "uf performing arts": (29.6365, -82.3693),
    "depot park": (29.6438, -82.3217),
    "gainesvilleshows.com": (29.6516, -82.3248),
    "heartwood soundstage": (29.6450, -82.3240),
    "glory days presents": (29.6516, -82.3248),
    "hippodrome theatre": (29.6513, -82.3244),
    "florida gators": (29.6499, -82.3486),
    "city of high springs": (29.8269, -82.5968),
    "city of alachua": (29.7936, -82.4937),
    "santa fe college": (29.6806, -82.4385),
    "celebration pointe": (29.6263, -82.4363),
    "greater gainesville chamber community events": (29.6514, -82.3248),
    "city of gainesville events directory": (29.6516, -82.3248),
    "alachua county meetings & events": (29.6516, -82.3248),
    "gainesville community events": (29.6516, -82.3248),
    "gainesville community events and activities": (29.6516, -82.3248),
    "things to do gainesville group": (29.6516, -82.3248),
    "things to do gainesville group (alt url)": (29.6516, -82.3248),
    "gainesville events facebook page": (29.6516, -82.3248),
    "fun 4 gator kids calendar": (29.6516, -82.3248),
    "mainstreet daily news events": (29.6516, -82.3248),
    "103.7 the gator community update": (29.6434, -82.3551),
    "eventbrite alachua events": (29.7936, -82.4937),
    "eventbrite gainesville events": (29.6516, -82.3248),
    "visit gainesville events": (29.6519, -82.3248),
    "visit gainesville festivals & special events": (29.6519, -82.3248),
    "celebration pointe events": (29.6263, -82.4363),
    "depot park events calendar": (29.6438, -82.3217),
    "high dive": (29.6521, -82.3243)
}

# Standard addresses for geocoder queries if not in predefined lookup
VENUE_ADDRESS_MAPPING = {
    "cade museum": "811 S Main St, Gainesville, FL 32601",
    "florida museum of natural history": "3215 Hull Rd, Gainesville, FL 32611",
    "harn museum of art": "3259 Hull Rd, Gainesville, FL 32611",
    "depot park": "874 SE 4th St, Gainesville, FL 32601",
    "heartwood soundstage": "619 S Main St, Gainesville, FL 32601",
    "hippodrome theatre": "25 SE 2nd Pl, Gainesville, FL 32601",
    "high dive": "210 SW 2nd Ave, Gainesville, FL 32601",
    "santa fe college": "3000 NW 83rd St, Gainesville, FL 32606",
    "celebration pointe": "4949 Celebration Pointe Ave, Gainesville, FL 32608",
    "alachua county library district": "401 E University Ave, Gainesville, FL 32601",
}

def geocode_venue(name, address=None):
    """
    Geocodes a single venue name/address.
    Utilizes predefined values, falling back to Nominatim API if not found, with safety defaults.
    """
    clean_name = name.lower().strip()

    # 1. Try direct exact match or keyword match in predefined coords
    for key, coords in PREDEFINED_COORDINATES.items():
        if key in clean_name or clean_name in key:
            return coords

    # 2. Try looking up custom address or venue name via Geocoder API
    query_address = address
    if not query_address:
        # Check if we have a known specific address for this venue
        for key, addr in VENUE_ADDRESS_MAPPING.items():
            if key in clean_name or clean_name in key:
                query_address = addr
                break

        # Fallback query
        if not query_address:
            query_address = f"{name}, Gainesville, FL"

    try:
        geolocator = Nominatim(user_agent="gainesville-events-map-agent")
        # Throttle request rate
        time.sleep(1.0)
        location = geolocator.geocode(query_address)
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        print(f"Geocoding error for '{query_address}': {e}")

    # 3. Safe fallback (Gainesville Center)
    return (29.6516, -82.3248)

if __name__ == "__main__":
    print("Testing geocoding logic...")
    print("Cade Museum ->", geocode_venue("Cade Museum"))
    print("Depot Park ->", geocode_venue("Depot Park"))
    print("Unknown Venue ->", geocode_venue("A totally new random venue in Gainesville"))
