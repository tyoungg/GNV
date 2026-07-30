import streamlit as st
import pandas as pd
import folium
import os
import re
import datetime
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Gainesville Events Map",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- App Header / Styling ---
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    @keyframes pulse-glow {
        0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.8); }
        70% { box-shadow: 0 0 0 12px rgba(220, 38, 38, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
    }
    .glow-active {
        animation: pulse-glow 2s infinite;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🗺️ Gainesville Events & Venues Map</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">An interactive guide mapping upcoming events to their actual physical locations across Gainesville. Aggregated from over 30+ local calendar sources on <a href="https://gainesvilleevents.com/sources/" target="_blank">GainesvilleEvents.com/sources</a>. View upcoming events, filter by categories, and find direct navigation!</div>', unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_data():
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "venues.csv"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "gainesville-events-map", "data", "venues.csv"),
        "gainesville-events-map/data/venues.csv",
        "data/venues.csv",
    ]

    csv_path = None
    for p in possible_paths:
        if os.path.exists(p):
            csv_path = p
            break

    if not csv_path:
        raise FileNotFoundError(f"Could not locate venues.csv. Tried paths: {possible_paths}")

    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["lat", "lon", "name"])
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading venue data: {e}")
    st.stop()

# --- Global Mappings ---
colors_mapping = {
    "Music": "#1E3A8A",      # Deep blue
    "Arts": "#7C3AED",       # Violet/Purple
    "Museum": "#059669",     # Emerald green
    "Library": "#D97706",    # Warm orange
    "Park": "#15803D",       # Dark green
    "Sports": "#0891B2",     # Cyan/Cadet blue
    "University": "#111827", # Charcoal/Black
    "Brewery": "#DC2626",    # Vibrant red
    "Other": "#4B5563"       # Slate gray
}

emojis_mapping = {
    "Music": "🎵",
    "Arts": "🎨",
    "Museum": "🏛️",
    "Library": "📚",
    "Park": "🌳",
    "Sports": "⚾",
    "University": "🎓",
    "Brewery": "🍺",
    "Other": "📍"
}

# --- Feature Enhancements & Live Event Parsing ---

PHYSICAL_VENUES = {
    # --- Library Branches ---
    "Headquarters Library": {
        "address": "401 E University Ave, Gainesville, FL 32601",
        "lat": 29.6515,
        "lon": -82.3244,
        "website": "https://www.aclib.us/headquarters",
        "category": "Library"
    },
    "Alachua Branch": {
        "address": "14913 NW 140th St, Alachua, FL 32615",
        "lat": 29.7941,
        "lon": -82.4941,
        "website": "https://www.aclib.us/alachua",
        "category": "Library"
    },
    "Archer Branch": {
        "address": "13550 SW 170th St, Archer, FL 32618",
        "lat": 29.5303,
        "lon": -82.5186,
        "website": "https://www.aclib.us/archer",
        "category": "Library"
    },
    "Cone Park Branch": {
        "address": "2801 E University Ave, Gainesville, FL 32641",
        "lat": 29.6521,
        "lon": -82.2887,
        "website": "https://www.aclib.us/conepark",
        "category": "Library"
    },
    "Hawthorne Branch": {
        "address": "20078 SE Hawthorn Rd, Hawthorne, FL 32640",
        "lat": 29.5931,
        "lon": -82.1105,
        "website": "https://www.aclib.us/hawthorne",
        "category": "Library"
    },
    "High Springs Branch": {
        "address": "23779 US-27, High Springs, FL 32643",
        "lat": 29.8272,
        "lon": -82.5975,
        "website": "https://www.aclib.us/highsprings",
        "category": "Library"
    },
    "Library Partnership Branch": {
        "address": "1130 NE 16th Ave, Gainesville, FL 32601",
        "lat": 29.6659,
        "lon": -82.3113,
        "website": "https://www.aclib.us/partnership",
        "category": "Library"
    },
    "Micanopy Branch": {
        "address": "706 NE Cholokka Blvd, Micanopy, FL 32667",
        "lat": 29.5056,
        "lon": -82.2794,
        "website": "https://www.aclib.us/micanopy",
        "category": "Library"
    },
    "Millhopper Branch": {
        "address": "3145 NW 43rd St, Gainesville, FL 32606",
        "lat": 29.6816,
        "lon": -82.3892,
        "website": "https://www.aclib.us/millhopper",
        "category": "Library"
    },
    "Newberry Branch": {
        "address": "110 South Seaboard Dr, Newberry, FL 32669",
        "lat": 29.6464,
        "lon": -82.6078,
        "website": "https://www.aclib.us/newberry",
        "category": "Library"
    },
    "Tower Road Branch": {
        "address": "3020 SW 75th St, Gainesville, FL 32608",
        "lat": 29.6253,
        "lon": -82.4239,
        "website": "https://www.aclib.us/towerroad",
        "category": "Library"
    },
    "Waldo Branch": {
        "address": "14257 Cole St, Waldo, FL 32694",
        "lat": 29.7891,
        "lon": -82.1678,
        "website": "https://www.aclib.us/waldo",
        "category": "Library"
    },

    # --- Other Physical Venues ---
    "Cade Museum": {
        "address": "811 S Main St, Gainesville, FL 32601",
        "lat": 29.6443,
        "lon": -82.3168,
        "website": "https://cademuseum.org/",
        "category": "Museum"
    },
    "Florida Museum of Natural History": {
        "address": "3215 Hull Rd, Gainesville, FL 32611",
        "lat": 29.6381,
        "lon": -82.3692,
        "website": "https://www.floridamuseum.ufl.edu/",
        "category": "Museum"
    },
    "Harn Museum of Art": {
        "address": "3259 Hull Rd, Gainesville, FL 32611",
        "lat": 29.6370,
        "lon": -82.3698,
        "website": "https://harn.ufl.edu/",
        "category": "Museum"
    },
    "UF Performing Arts": {
        "address": "3201 Hull Rd, Gainesville, FL 32611",
        "lat": 29.6365,
        "lon": -82.3693,
        "website": "https://performingarts.ufl.edu/",
        "category": "Arts"
    },
    "Depot Park": {
        "address": "874 SE 4th St, Gainesville, FL 32601",
        "lat": 29.6438,
        "lon": -82.3217,
        "website": "https://www.depotpark.org/",
        "category": "Park"
    },
    "Heartwood Soundstage": {
        "address": "619 S Main St, Gainesville, FL 32601",
        "lat": 29.6450,
        "lon": -82.3240,
        "website": "https://www.heartwoodsoundstage.com/",
        "category": "Music"
    },
    "Hippodrome Theatre": {
        "address": "25 SE 2nd Pl, Gainesville, FL 32601",
        "lat": 29.6513,
        "lon": -82.3244,
        "website": "https://thehipp.org/",
        "category": "Arts"
    },
    "High Dive": {
        "address": "210 SW 2nd Ave, Gainesville, FL 32601",
        "lat": 29.6521,
        "lon": -82.3243,
        "website": "https://highdivegville.com/",
        "category": "Music"
    },
    "Celebration Pointe": {
        "address": "4949 Celebration Pointe Ave, Gainesville, FL 32608",
        "lat": 29.6263,
        "lon": -82.4363,
        "website": "https://www.celebrationpointe.com/",
        "category": "Other"
    },
    "Santa Fe College": {
        "address": "3000 NW 83rd St, Gainesville, FL 32606",
        "lat": 29.6806,
        "lon": -82.4385,
        "website": "https://www.sfcollege.edu/",
        "category": "University"
    },
    "Bo Diddley Plaza": {
        "address": "111 E University Ave, Gainesville, FL 32601",
        "lat": 29.6515,
        "lon": -82.3248,
        "website": "https://www.bodiddleyplaza.com/",
        "category": "Park"
    },
    "First Magnitude Brewing Company": {
        "address": "1220 SE Veitch St, Gainesville, FL 32601",
        "lat": 29.6402,
        "lon": -82.3238,
        "website": "https://fmbrew.com/",
        "category": "Brewery"
    },
    "Cypress & Grove Brewing Co.": {
        "address": "512 NW 4th St, Gainesville, FL 32601",
        "lat": 29.6558,
        "lon": -82.3292,
        "website": "https://cypressandgrove.com/",
        "category": "Brewery"
    },
    "Reitz Union Lawn": {
        "address": "655 Reitz Union Drive, Gainesville, FL 32611",
        "lat": 29.6463,
        "lon": -82.3478,
        "website": "https://www.union.ufl.edu/",
        "category": "Arts"
    },
    "Ben Hill Griffin Stadium": {
        "address": "157 Gale Lemerand Dr, Gainesville, FL 32611",
        "lat": 29.6499,
        "lon": -82.3487,
        "website": "https://floridagators.com/facilities/ben-hill-griffin-stadium/1",
        "category": "Sports"
    },
    "Stephen C. O'Connell Center": {
        "address": "250 Gale Lemerand Dr, Gainesville, FL 32611",
        "lat": 29.6494,
        "lon": -82.3512,
        "website": "https://www.oconnellcenter.com/",
        "category": "Sports"
    },
    "Sweetwater Wetlands Park": {
        "address": "3215 SE Williston Rd, Gainesville, FL 32641",
        "lat": 29.6225,
        "lon": -82.3015,
        "website": "https://www.gainesvillefl.gov/Parks-Conservation-Recreation/Sweetwater-Wetlands-Park",
        "category": "Park"
    },
    "The Wooly": {
        "address": "20 N Main St, Gainesville, FL 32601",
        "lat": 29.6515,
        "lon": -82.3253,
        "website": "https://thewooly.com/",
        "category": "Arts"
    },
    "Tioga Town Center": {
        "address": "13085 SW 1st Lane, Newberry, FL 32669",
        "lat": 29.6493,
        "lon": -82.4725,
        "website": "https://www.tiogatowncenter.com/",
        "category": "Other"
    },
    "High Springs Playhouse": {
        "address": "23414 W US Hwy 27, High Springs, FL 32643",
        "lat": 29.8275,
        "lon": -82.5955,
        "website": "https://highspringplayhouse.com/",
        "category": "Arts"
    },
    "Gainesville Community Playhouse": {
        "address": "1900 NE 16th Ave, Gainesville, FL 32609",
        "lat": 29.6661,
        "lon": -82.3025,
        "website": "https://gcplayhouse.org/",
        "category": "Arts"
    },
    "Acrosstown Repertory Theatre": {
        "address": "3501 SW 2nd Ave, Gainesville, FL 32607",
        "lat": 29.6508,
        "lon": -82.3745,
        "website": "https://acrosstown.org/",
        "category": "Arts"
    },
    "Loosey's": {
        "address": "120 SW 1st Ave, Gainesville, FL 32601",
        "lat": 29.6510,
        "lon": -82.3255,
        "website": "https://looseys.com/",
        "category": "Music"
    },
    "The Atlantic": {
        "address": "15 N Main St, Gainesville, FL 32601",
        "lat": 29.6515,
        "lon": -82.3248,
        "website": "https://theatlanticgainesville.com/",
        "category": "Music"
    },
    "Signal": {
        "address": "104 S Main St, Gainesville, FL 32601",
        "lat": 29.6505,
        "lon": -82.3248,
        "website": "https://signalgainesville.com/",
        "category": "Music"
    },
    "Rosa B. Williams Center": {
        "address": "524 NW 1st St, Gainesville, FL 32601",
        "lat": 29.6559,
        "lon": -82.3255,
        "website": "https://www.gainesvillefl.gov/Parks-Conservation-Recreation/Rosa-B-Williams-Center",
        "category": "Arts"
    },
    "High Springs Brewing Company": {
        "address": "18562 NW 237th St, High Springs, FL 32643",
        "lat": 29.8268,
        "lon": -82.5965,
        "website": "https://highspringsbrewing.com/",
        "category": "Brewery"
    },
    "Swamp Head Brewery": {
        "address": "3650 SW 42nd Ave, Gainesville, FL 32608",
        "lat": 29.6198,
        "lon": -82.3780,
        "website": "https://swamphead.com/",
        "category": "Brewery"
    },
    "Blackadder Brewing Company": {
        "address": "618 NW 60th St, Gainesville, FL 32607",
        "lat": 29.6582,
        "lon": -82.4082,
        "website": "https://www.blackadderbrewing.com/",
        "category": "Brewery"
    },
    "Civic Media Center": {
        "address": "433 S Main St, Gainesville, FL 32601",
        "lat": 29.6474,
        "lon": -82.3248,
        "website": "https://www.civicmediacenter.org/",
        "category": "Library"
    },
    "Donald R. Dizney Stadium": {
        "address": "2580 Hull Rd, Gainesville, FL 32611",
        "lat": 29.6366,
        "lon": -82.3725,
        "website": "https://floridagators.com/facilities/donald-r-dizney-stadium/7",
        "category": "Sports"
    },
    "4th Ave Food Park": {
        "address": "409 SW 4th Ave, Gainesville, FL 32601",
        "lat": 29.6481,
        "lon": -82.3292,
        "website": "https://4thavefoodpark.com/",
        "category": "Other"
    },
    "Baby J's Bar": {
        "address": "7 W University Ave, Gainesville, FL 32601",
        "lat": 29.6515,
        "lon": -82.3252,
        "website": "https://babyjsbar.com/",
        "category": "Music"
    },
    "The Bull": {
        "address": "18 SW 1st Ave, Gainesville, FL 32601",
        "lat": 29.6511,
        "lon": -82.3249,
        "website": "https://thebullgainesville.com/",
        "category": "Music"
    },
    "Skinner Park": {
        "address": "NW Skinner Ter, Alachua, FL 32615",
        "lat": 29.7745,
        "lon": -82.4785,
        "website": "https://www.cityofalachua.com/",
        "category": "Park"
    },
    "Aloft Hotel Gainesville": {
        "address": "3743 Hull Rd, Gainesville, FL 32607",
        "lat": 29.6385,
        "lon": -82.3792,
        "website": "https://www.marriott.com/en-us/hotels/gnval-aloft-gainesville-university-area/",
        "category": "Other"
    }
}

def parse_ics_datetime(dt_str):
    try:
        clean_str = dt_str.replace("T", "").replace("Z", "")
        if len(clean_str) >= 14:
            return datetime.datetime.strptime(clean_str[:14], "%Y%m%d%H%M%S")
        elif len(clean_str) >= 8:
            return datetime.datetime.strptime(clean_str[:8], "%Y%m%d")
    except Exception:
        pass
    return None

def format_time_range(start_dt, end_dt):
    if not start_dt:
        return "All Day"

    local_start = start_dt - datetime.timedelta(hours=4)
    start_str = local_start.strftime("%-I:%M %p")

    if end_dt:
        local_end = end_dt - datetime.timedelta(hours=4)
        end_str = local_end.strftime("%-I:%M %p")
        return f"{start_str} – {end_str}"

    return start_str

@st.cache_data
def load_real_events(today_str):
    import requests
    url = "https://gainesvilleevents.com/feed.ics"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        st.error(f"Error fetching live event feed: {e}")
        return []

    events = []
    current_event = {}
    in_vevent = False

    lines = []
    for line in content.splitlines():
        if line.startswith(" ") and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)

    for line in lines:
        if line.startswith("BEGIN:VEVENT"):
            current_event = {}
            in_vevent = True
        elif line.startswith("END:VEVENT"):
            if in_vevent:
                events.append(current_event)
            in_vevent = False
        elif in_vevent:
            if ":" in line:
                key, val = line.split(":", 1)
                if ";" in key:
                    key = key.split(";", 1)[0]
                current_event[key] = val

    parsed_events = []
    base_date = datetime.date.fromisoformat(today_str)

    for ev in events:
        summary = ev.get("SUMMARY", "").replace("\\,", ",").replace("\\;", ";").strip()
        location = ev.get("LOCATION", "").replace("\\,", ",").replace("\\;", ";").strip()
        description = ev.get("DESCRIPTION", "").replace("\\,", ",").replace("\\;", ";").strip()
        url = ev.get("URL", "").strip()

        dtstart_str = ev.get("DTSTART", "")
        dtstart = parse_ics_datetime(dtstart_str)
        if not dtstart:
            continue

        dtend_str = ev.get("DTEND", "")
        dtend = parse_ics_datetime(dtend_str)

        local_dtstart = dtstart - datetime.timedelta(hours=4)
        event_date = local_dtstart.date()

        days_away = (event_date - base_date).days
        if days_away < 0:
            continue

        event_date_str = event_date.strftime("%A, %B %d, %Y")

        if days_away == 0:
            timeframe = "Today"
        elif event_date.weekday() in [4, 5, 6] and days_away <= (6 - base_date.weekday()):
            timeframe = "This Weekend"
        elif days_away <= 7:
            timeframe = "Next 7 Days"
        else:
            timeframe = "Later"

        time_range = format_time_range(dtstart, dtend)

        tag = "Other"
        description_lower = description.lower()
        summary_lower = summary.lower()

        if "music" in description_lower or "music" in summary_lower or "concert" in description_lower or "show" in description_lower or "band" in description_lower or "sing" in description_lower:
            tag = "Music"
        elif "art" in description_lower or "theatre" in description_lower or "theater" in description_lower or "dance" in description_lower or "comedy" in description_lower:
            tag = "Arts"
        elif "museum" in description_lower or "exhibit" in description_lower:
            tag = "Museum"
        elif "library" in description_lower or "book" in description_lower or "story" in description_lower or "read" in description_lower:
            tag = "Library"
        elif "park" in description_lower or "walk" in description_lower or "outdoors" in description_lower or "nature" in description_lower:
            tag = "Park"
        elif "sports" in description_lower or "gators" in description_lower or "game" in description_lower or "pickleball" in description_lower:
            tag = "Sports"
        elif "university" in description_lower or "college" in description_lower or "campus" in description_lower:
            tag = "University"
        elif "brewery" in description_lower or "beer" in description_lower or "pub" in description_lower:
            tag = "Brewery"

        cost = "FREE"
        if "$" in description:
            prices = re.findall(r"\$\d+", description)
            if prices:
                cost = prices[0]
            else:
                cost = "PAID"

        event_venue_name = "General Gainesville"
        event_lat = 29.6516
        event_lon = -82.3248
        event_address = "Gainesville, FL"

        matched_venue_key = None
        for key in PHYSICAL_VENUES.keys():
            if key.lower() in location.lower() or location.lower() in key.lower():
                matched_venue_key = key
                break

        if not matched_venue_key:
            loc_lower = location.lower()
            if "alachua branch" in loc_lower or "alachua library" in loc_lower:
                matched_venue_key = "Alachua Branch"
            elif "archer branch" in loc_lower or "archer library" in loc_lower:
                matched_venue_key = "Archer Branch"
            elif "cone park" in loc_lower:
                matched_venue_key = "Cone Park Branch"
            elif "hawthorne branch" in loc_lower or "hawthorne library" in loc_lower:
                matched_venue_key = "Hawthorne Branch"
            elif "high springs branch" in loc_lower or "high springs library" in loc_lower:
                matched_venue_key = "High Springs Branch"
            elif "library partnership" in loc_lower:
                matched_venue_key = "Library Partnership Branch"
            elif "micanopy branch" in loc_lower or "micanopy library" in loc_lower:
                matched_venue_key = "Micanopy Branch"
            elif "millhopper branch" in loc_lower or "millhopper library" in loc_lower:
                matched_venue_key = "Millhopper Branch"
            elif "newberry branch" in loc_lower or "newberry library" in loc_lower:
                matched_venue_key = "Newberry Branch"
            elif "tower road branch" in loc_lower or "tower road library" in loc_lower:
                matched_venue_key = "Tower Road Branch"
            elif "waldo branch" in loc_lower or "waldo library" in loc_lower:
                matched_venue_key = "Waldo Branch"
            elif "headquarters" in loc_lower or "hq library" in loc_lower:
                matched_venue_key = "Headquarters Library"
            elif "dizney stadium" in loc_lower:
                matched_venue_key = "Donald R. Dizney Stadium"
            elif "o'connell" in loc_lower or "oconnell" in loc_lower:
                matched_venue_key = "Stephen C. O'Connell Center"
            elif "ben hill griffin" in loc_lower or "griffin stadium" in loc_lower:
                matched_venue_key = "Ben Hill Griffin Stadium"
            elif "wool" in loc_lower:
                matched_venue_key = "The Wooly"
            elif "plaza" in loc_lower:
                matched_venue_key = "Bo Diddley Plaza"
            elif "hippodrome" in loc_lower:
                matched_venue_key = "Hippodrome Theatre"
            elif "cade" in loc_lower:
                matched_venue_key = "Cade Museum"
            elif "museum of natural history" in loc_lower:
                matched_venue_key = "Florida Museum of Natural History"
            elif "harn" in loc_lower:
                matched_venue_key = "Harn Museum of Art"
            elif "performing arts" in loc_lower:
                matched_venue_key = "UF Performing Arts"
            elif "depot park" in loc_lower:
                matched_venue_key = "Depot Park"
            elif "heartwood" in loc_lower:
                matched_venue_key = "Heartwood Soundstage"
            elif "high dive" in loc_lower:
                matched_venue_key = "High Dive"
            elif "celebration" in loc_lower:
                matched_venue_key = "Celebration Pointe"
            elif "santa fe" in loc_lower or "sf college" in loc_lower:
                matched_venue_key = "Santa Fe College"
            elif "tioga" in loc_lower:
                matched_venue_key = "Tioga Town Center"
            elif "first magnitude" in loc_lower:
                matched_venue_key = "First Magnitude Brewing Company"
            elif "cypress & grove" in loc_lower:
                matched_venue_key = "Cypress & Grove Brewing Co."
            elif "blackadder" in loc_lower:
                matched_venue_key = "Blackadder Brewing Company"
            elif "swamp head" in loc_lower:
                matched_venue_key = "Swamp Head Brewery"
            elif "civic media" in loc_lower:
                matched_venue_key = "Civic Media Center"
            elif "loosey" in loc_lower:
                matched_venue_key = "Loosey's"
            elif "atlantic" in loc_lower:
                matched_venue_key = "The Atlantic"
            elif "signal" in loc_lower:
                matched_venue_key = "Signal"
            elif "rosa b." in loc_lower:
                matched_venue_key = "Rosa B. Williams Center"

        if matched_venue_key:
            v_info = PHYSICAL_VENUES[matched_venue_key]
            event_venue_name = matched_venue_key
            event_lat = v_info["lat"]
            event_lon = v_info["lon"]
            event_address = v_info["address"]
        else:
            event_venue_name = location if location else "Other Location"
            event_lat = 29.6516
            event_lon = -82.3248
            event_address = location if location else "Gainesville, FL"

        source_name = "Visit Gainesville"
        uid = ev.get("UID", "").lower()
        if "aclibrary" in uid or "library" in description_lower:
            source_name = "Alachua County Library District"
        elif "cademuseum" in uid:
            source_name = "Cade Museum"
        elif "floridamuseum" in uid:
            source_name = "Florida Museum of Natural History"
        elif "gainesvilleshows" in uid:
            source_name = "GainesvilleShows.com"
        elif "harn" in uid:
            source_name = "Harn Museum of Art"
        elif "heartwood" in uid:
            source_name = "Heartwood Soundstage"
        elif "hippodrome" in uid:
            source_name = "Hippodrome Theatre"
        elif "tioga" in uid:
            source_name = "Tioga Town Center"
        elif "visitgainesville" in uid:
            source_name = "Visit Gainesville"
        elif "floridagators" in uid:
            source_name = "Florida Gators"
        elif "santafecollege" in uid:
            source_name = "Santa Fe College"
        elif "depotpark" in uid:
            source_name = "Depot Park"

        parsed_events.append({
            "title": summary,
            "tag": tag,
            "timeframe": timeframe,
            "days_away": days_away,
            "date_str": event_date_str,
            "time_range": time_range,
            "cost": cost,
            "event_venue": event_venue_name,
            "event_lat": event_lat,
            "event_lon": event_lon,
            "event_address": event_address,
            "source_name": source_name,
            "description": description if description else f"Join us at {event_address} for this event!",
            "website": url
        })

    return parsed_events

# Ensure we pass today's date dynamically
today_str = datetime.date.today().isoformat()
active_raw_events = load_real_events(today_str)

# --- Sidebar Controls ---
st.sidebar.header("Filter & Settings")

# 1. Search Bar
search_query = st.sidebar.text_input("🔍 Search (Venue/Event)", "")

# 2. Category Selection
categories = sorted(list(colors_mapping.keys()))
selected_categories = st.sidebar.multiselect(
    "📂 Venue Categories",
    categories,
    default=categories
)

# 3. Time Slider
time_filter = st.sidebar.select_slider(
    "📅 Event Time Horizon",
    options=["All", "Next 7 Days", "This Weekend", "Today"]
)

# 4. Map View Toggle
map_view_type = st.sidebar.radio(
    "🗺️ Map View Mode",
    ["Standard Pin Cluster", "Density Heatmap"]
)

# 5. Geolocation / "Near Me" Simulation
st.sidebar.markdown("---")
st.sidebar.subheader("📍 Geolocation Simulation")
near_me_enabled = st.sidebar.checkbox("Simulate 'Near Me' GPS Location")

# Standard coordinates for simulation
user_lat = 29.6450
user_lon = -82.3240

if near_me_enabled:
    st.sidebar.info("🎯 Simulating location near Heartwood Soundstage (South Downtown Gainesville). Only venues within ~2.5 miles are highlighted in the list!")

# --- Map Legend ---
st.sidebar.markdown("---")
st.sidebar.subheader("🎨 Map Legend")
legend_html = '<div style="font-family: \'Helvetica Neue\', Arial, sans-serif; font-size: 0.85rem; line-height: 1.6;">'
for category_name, hex_color in colors_mapping.items():
    emoji = emojis_mapping.get(category_name, "📍")
    legend_html += f'<div style="display: flex; align-items: center; margin-bottom: 6px;"><span style="background-color: {hex_color}; border-radius: 50%; width: 14px; height: 14px; display: inline-block; margin-right: 8px; border: 1px solid white; box-shadow: 0px 1px 3px rgba(0,0,0,0.2);"></span><span>{emoji} <b>{category_name}</b></span></div>'

legend_html += '<div style="margin-top: 10px; border-top: 1px solid #E5E7EB; padding-top: 8px; display: flex; align-items: center; gap: 8px;"><span class="glow-active" style="background-color: #DC2626; border-radius: 50%; width: 14px; height: 14px; display: inline-block; border: 2px solid #FF3B30;"></span><span style="font-size: 0.75rem; color: #DC2626; font-weight: bold;">Pulse: Event Today!</span></div></div>'
st.sidebar.markdown(legend_html, unsafe_allow_html=True)

# --- Filter Logic ---
active_events = []
for ev in active_raw_events:
    phys_venue_name = ev["event_venue"]
    phys_venue_info = PHYSICAL_VENUES.get(phys_venue_name, {
        "category": "Other",
        "lat": ev["event_lat"],
        "lon": ev["event_lon"]
    })
    phys_venue_cat = phys_venue_info.get("category", "Other")

    # 1. Category Filter
    if phys_venue_cat not in selected_categories:
        continue

    # 2. Search Query Filter
    if search_query:
        query = search_query.lower()
        match_venue = query in phys_venue_name.lower()
        match_title = query in ev["title"].lower()
        match_source = query in ev["source_name"].lower()
        if not (match_venue or match_title or match_source):
            continue

    # 3. Time Filter
    if time_filter != "All":
        if time_filter == "Today" and ev["timeframe"] != "Today":
            continue
        elif time_filter == "This Weekend" and ev["timeframe"] not in ["Today", "This Weekend"]:
            continue
        elif time_filter == "Next 7 Days" and ev["timeframe"] not in ["Today", "This Weekend", "Next 7 Days"]:
            continue

    # 4. Near Me Filter
    if near_me_enabled:
        dist = ((ev["event_lat"] - user_lat)**2 + (ev["event_lon"] - user_lon)**2)**0.5
        if dist > 0.036:
            continue

    active_events.append(ev)

# Sort all active events chronologically by days_away
active_events.sort(key=lambda x: x["days_away"])

# Group active events by physical venue
events_by_physical_venue = {}
for ev in active_events:
    venue_name = ev["event_venue"]
    if venue_name not in events_by_physical_venue:
        events_by_physical_venue[venue_name] = []
    events_by_physical_venue[venue_name].append(ev)

# Create summary of active venues
active_venues_data = []
for name, v_events in events_by_physical_venue.items():
    v_info = PHYSICAL_VENUES.get(name, {
        "address": v_events[0]["event_address"],
        "lat": v_events[0]["event_lat"],
        "lon": v_events[0]["event_lon"],
        "website": "https://gainesvilleevents.com/",
        "category": "Other"
    })
    active_venues_data.append({
        "name": name,
        "category": v_info["category"],
        "lat": v_info["lat"],
        "lon": v_info["lon"],
        "website": v_info["website"],
        "address": v_info["address"],
        "description": f"Venue located at {v_info['address']}."
    })
filtered = pd.DataFrame(active_venues_data) if active_venues_data else pd.DataFrame(columns=["name", "category", "lat", "lon", "website", "address", "description"])

# --- Initialize Session State for Active Venue ---
if "selected_venue" not in st.session_state:
    active_physical_venue_names = sorted(list(events_by_physical_venue.keys())) if events_by_physical_venue else sorted(list(PHYSICAL_VENUES.keys()))
    st.session_state["selected_venue"] = active_physical_venue_names[0]

# --- Metrics section ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Venues Selected", len(filtered))
with col2:
    # Deduplicate active events by title, date, and venue to count unique physical events
    unique_active_events_count = len(set((ev["title"].lower().strip(), ev["date_str"], ev["event_venue"]) for ev in active_events))
    st.metric("Total Match Events Found", unique_active_events_count)
with col3:
    st.metric("Active Categories", len(filtered["category"].unique()) if len(filtered) > 0 else 0)

# --- Build Folium Map ---
m = folium.Map(
    location=[29.6516, -82.3248],
    zoom_start=13,
    tiles="CartoDB positron"
)

if near_me_enabled:
    folium.Marker(
        [user_lat, user_lon],
        popup="<b>You are here (Simulated)</b>",
        tooltip="Your Location",
        icon=folium.Icon(color="red", icon="user", prefix="fa")
    ).add_to(m)

if map_view_type == "Standard Pin Cluster":
    cluster = MarkerCluster().add_to(m)
    for _, row in filtered.iterrows():
        name = row["name"]
        cat = row["category"]
        url = row["website"]
        lat = row["lat"]
        lon = row["lon"]
        desc = row.get("description", "")
        address = row.get("address", "")

        v_events = events_by_physical_venue.get(name, [])
        unique_events_count = len(set((ev["title"].lower().strip(), ev["date_str"]) for ev in v_events))
        emoji = emojis_mapping.get(cat, "📍")

        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
        desc_html = f'<p style="font-size: 0.85rem; color: #4B5563; margin: 8px 0 4px 0;"><i>{desc}</i></p>'

        events_html = ""
        if v_events:
            events_html += '<div style="border-top: 1px solid #E5E7EB; margin-top: 10px; padding-top: 10px; font-family: \'Helvetica Neue\', Arial, sans-serif; line-height: 1.4; max-height: 180px; overflow-y: auto;">'
            events_html += f'<div style="font-weight: bold; font-size: 0.9rem; color: #374151; margin-bottom: 6px;">Upcoming Events ({unique_events_count}):</div>'

            # De-duplicate for card presentation
            seen_events = set()
            presented_count = 0
            for ev in v_events:
                ev_key = (ev['title'].lower().strip(), ev['date_str'])
                if ev_key in seen_events:
                    continue
                seen_events.add(ev_key)
                presented_count += 1
                if presented_count > 3:
                    continue

                events_html += f"""
                <div style="margin-bottom: 8px; border-bottom: 1px dashed #F3F4F6; padding-bottom: 6px;">
                    <div style="font-weight: bold; font-size: 0.85rem; color: #1F2937; margin-bottom: 2px;">{ev['title']}</div>
                    <div style="color: #4B5563; font-size: 0.8rem; margin-bottom: 2px;">{ev['date_str']}, {ev['time_range']}</div>
                    <div style="color: #4B5563; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 2px;">{ev['tag']} · <span style="color: #059669;">{ev['cost']}</span></div>
                    <div style="color: #2563EB; font-size: 0.75rem;">Source: {ev['source_name']}</div>
                </div>
                """
            if unique_events_count > 3:
                events_html += f'<div style="font-size: 0.75rem; color: #6B7280; text-align: center;">+ {unique_events_count - 3} more events (see below)</div>'
            events_html += '</div>'

        popup_html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; min-width: 220px;">
            <h4 style="margin: 0 0 5px 0; color: #1E3A8A;">{emoji} {name}</h4>
            <span style="background-color: #F3F4F6; color: #374151; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">{cat} Venue</span>
            {desc_html}
            {events_html}
            <div style="margin-top: 12px; border-top: 1px solid #E5E7EB; padding-top: 8px; display: flex; gap: 6px;">
                <a href="{url}" target="_blank" style="background-color: #2563EB; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 0.8rem;">Website</a>
                <a href="{directions_url}" target="_blank" style="background-color: #059669; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 0.8rem;">Directions</a>
            </div>
        </div>
        """

        tooltip_text = f"{name} ({unique_events_count} active events)" if v_events else name

        has_today = any(ev["timeframe"] == "Today" for ev in v_events)
        glow_class = "glow-active" if has_today else ""
        border_style = "border: 2px solid #FFFFFF;"
        if has_today:
            border_style = "border: 2.5px solid #FF3B30;"

        marker_color = colors_mapping.get(cat, "#4B5563")
        event_count = unique_events_count

        pin_content = f"""
        <div class="{glow_class}" style="
            background-color: {marker_color};
            {border_style}
            border-radius: 50%;
            color: white;
            font-weight: 800;
            font-size: 11px;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0px 3px 6px rgba(0,0,0,0.3);
            font-family: 'Helvetica Neue', Arial, sans-serif;
        ">
            {event_count}
        </div>
        """

        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip_text,
            icon=folium.DivIcon(
                html=pin_content,
                icon_size=(32, 32),
                icon_anchor=(16, 16)
            )
        ).add_to(cluster)
else:
    heat_data = []
    for _, row in filtered.iterrows():
        name = row["name"]
        v_events = events_by_physical_venue.get(name, [])
        heat_data.append([row["lat"], row["lon"], float(len(v_events))])
    if heat_data:
        HeatMap(heat_data, radius=25, blur=15).add_to(m)

map_data = st_folium(
    m,
    use_container_width=True,
    height=550,
    key="gainesville_map"
)

# --- Click Handler ---
if map_data and map_data.get("last_object_clicked_tooltip"):
    clicked_venue = map_data["last_object_clicked_tooltip"]
    if " (" in clicked_venue and clicked_venue.endswith(" active events)"):
        clicked_venue = clicked_venue.split(" (")[0]
    if clicked_venue in filtered["name"].values:
        st.session_state["selected_venue"] = clicked_venue

# --- Click Interaction / Venue Details Sidebar & Tabbed Schedules ---
st.markdown("---")
st.subheader("🗓️ Venue Explorer & Full Schedule")

if len(filtered) == 0:
    st.warning("No physical venues found matching the current filters.")
else:
    tab1, tab2 = st.tabs(["📅 Full Schedule (All Selected Venues)", "📍 Individual Venue Explorer"])

    with tab1:
        st.markdown(f"**Showing all {unique_active_events_count} unique events across all {len(filtered)} active physical venues matching the \"{time_filter}\" horizon.**")
        if not active_events:
            st.info("No events scheduled across any of the selected venues in this time horizon.")
        else:
            # Chronological sorted unique list presentation
            seen_events = set()
            for ev in active_events:
                ev_key = (ev['title'].lower().strip(), ev['date_str'], ev['event_venue'])
                if ev_key in seen_events:
                    continue
                seen_events.add(ev_key)

                ev_directions_url = f"https://www.google.com/maps/dir/?api=1&destination={ev['event_lat']},{ev['event_lon']}"
                event_website = ev.get("website", "https://gainesvilleevents.com")

                st.markdown(f"""
                <div style="background-color: #F9FAFB; border-left: 4px solid #1E3A8A; padding: 12px; margin-bottom: 12px; border-radius: 0 4px 4px 0; font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.5;">
                    <div style="font-weight: bold; font-size: 1.05rem; color: #1F2937; margin-bottom: 2px;"><a href="{event_website}" target="_blank" style="text-decoration: none; color: #1F2937;">{ev['title']}</a></div>
                    <div style="color: #4B5563; font-size: 0.9rem; margin-bottom: 4px;">{ev['date_str']}, {ev['time_range']} · <b>{ev['event_venue']}</b></div>
                    <div style="color: #4B5563; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 2px;">{ev['tag']} · <a href="{ev_directions_url}" target="_blank" style="color: #059669; text-decoration: none;">🚗 Directions to Event Venue</a></div>
                    <div style="color: #059669; font-weight: bold; font-size: 0.8rem; margin-bottom: 2px;">{ev['cost']}</div>
                    <div style="color: #2563EB; font-size: 0.85rem; font-weight: 500;">Calendar Source: {ev['source_name']}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        venue_list = sorted(filtered["name"].unique()) if not filtered.empty else sorted(list(PHYSICAL_VENUES.keys()))
        current_selected = st.session_state["selected_venue"]
        if current_selected not in venue_list:
            current_selected = venue_list[0]
            st.session_state["selected_venue"] = current_selected

        selected_venue_idx = venue_list.index(current_selected)

        selected_venue_name = st.selectbox(
            "Select a venue to inspect its upcoming events:",
            venue_list,
            index=selected_venue_idx,
            key="venue_selectbox"
        )
        st.session_state["selected_venue"] = selected_venue_name

        venue_data = filtered[filtered["name"] == selected_venue_name].iloc[0] if not filtered.empty and selected_venue_name in filtered["name"].values else None
        if venue_data is not None:
            st.markdown(f"### {emojis_mapping.get(venue_data['category'], '📍')} {venue_data['name']}")

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**Category:** {venue_data['category']}")
                st.markdown(f"**Website:** [Visit Official Website]({venue_data['website']})")
                st.markdown(f"📍 **Address:** {venue_data['address']}")
                directions_link = f"https://www.google.com/maps/dir/?api=1&destination={venue_data['lat']},{venue_data['lon']}"
                st.markdown(f"🚗 [Get Google Maps Directions]({directions_link})")

            with col2:
                st.markdown("**Upcoming Events Schedule:**")
                venue_events = events_by_physical_venue.get(selected_venue_name, [])
                if not venue_events:
                    st.write("No events scheduled for this venue in the selected time horizon.")
                else:
                    seen_venue_events = set()
                    for ev in venue_events:
                        ev_key = (ev['title'].lower().strip(), ev['date_str'])
                        if ev_key in seen_venue_events:
                            continue
                        seen_venue_events.add(ev_key)

                        ev_directions_url = f"https://www.google.com/maps/dir/?api=1&destination={ev['event_lat']},{ev['event_lon']}"
                        event_website = ev.get("website", "https://gainesvilleevents.com")

                        st.markdown(f"""
                        <div style="background-color: #F9FAFB; border-left: 4px solid #3B82F6; padding: 12px; margin-bottom: 12px; border-radius: 0 4px 4px 0; font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.5;">
                            <div style="font-weight: bold; font-size: 1.05rem; color: #1F2937; margin-bottom: 2px;"><a href="{event_website}" target="_blank" style="text-decoration: none; color: #1F2937;">{ev['title']}</a></div>
                            <div style="color: #4B5563; font-size: 0.9rem; margin-bottom: 4px;">{ev['date_str']}, {ev['time_range']} · <b>{ev['event_venue']}</b></div>
                            <div style="color: #4B5563; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 2px;">{ev['tag']} · <a href="{ev_directions_url}" target="_blank" style="color: #3B82F6; text-decoration: none;">🚗 Directions to Event Venue</a></div>
                            <div style="color: #059669; font-weight: bold; font-size: 0.8rem; margin-bottom: 2px;">{ev['cost']}</div>
                            <div style="color: #2563EB; font-size: 0.85rem; font-weight: 500;">Calendar Source: {ev['source_name']}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No active matching events found at this venue, but here are the static details:")
            v_info = PHYSICAL_VENUES.get(selected_venue_name, {})
            st.markdown(f"### {emojis_mapping.get(v_info.get('category', 'Other'), '📍')} {selected_venue_name}")
            st.markdown(f"**Category:** {v_info.get('category', 'Other')}")
            st.markdown(f"**Website:** [Visit Official Website]({v_info.get('website', '#')})")
            st.markdown(f"📍 **Address:** {v_info.get('address', 'Gainesville, FL')}")
