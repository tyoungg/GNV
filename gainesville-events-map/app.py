import streamlit as st
import pandas as pd
import folium
import random
import os
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
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🗺️ Gainesville Event Sources Map</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">An interactive guide to the local calendars and venues feeding GainesvilleEvents.com. Pinpoint event sources, explore categories, view upcoming events, and find directions!</div>', unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_data():
    # Multi-path fallbacks to guarantee venues.csv is found regardless of wrapper/environment setup
    possible_paths = [
        # Relative to current file's directory (direct execution)
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "venues.csv"),
        # Relative to current file's directory with subdirectory (wrapped execution on Streamlit Cloud)
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "gainesville-events-map", "data", "venues.csv"),
        # Working directory with subfolder
        "gainesville-events-map/data/venues.csv",
        # Working directory direct
        "data/venues.csv",
    ]

    csv_path = None
    for p in possible_paths:
        if os.path.exists(p):
            csv_path = p
            break

    if not csv_path:
        # Fallback to display the tried paths if none was found
        raise FileNotFoundError(f"Could not locate venues.csv. Tried paths: {possible_paths}")

    df = pd.read_csv(csv_path)
    # Clean up empty or corrupted values
    df = df.dropna(subset=["lat", "lon", "name"])
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading venue data: {e}")
    st.stop()

# --- Feature Enhancements & Mock Data Generation ---

# A precise registry of physical hosting venues in Gainesville with coordinates and addresses.
# This prevents online portal coordinates (general city centers) from being used for actual event directions.
PHYSICAL_VENUES = {
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
    "Alachua County Library District": {
        "address": "401 E University Ave, Gainesville, FL 32601",
        "lat": 29.6515,
        "lon": -82.3244,
        "website": "https://www.aclib.us/",
        "category": "Library"
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
    }
}

# Note: Streamlit's @st.cache_data tries to hash input parameters.
# Passing a NumPy array (like df["name"].unique()) can throw UnhashableParamError in some Streamlit environments.
# Converting the parameter to a standard Python tuple or loading it inside avoids caching issues.
@st.cache_data
def generate_mock_events(venue_names_tuple, today_str):
    import datetime
    random.seed(42)  # For consistent results
    categories_pool = ["Music", "Theater", "Family", "Outdoor", "Food & Drink", "Community"]
    events = {}

    base_date = datetime.date.fromisoformat(today_str)
    today_weekday = base_date.weekday()  # Monday=0, Sunday=6

    for name in venue_names_tuple:
        num_events = random.randint(1, 15)
        venue_events = []

        # Check if the source name represents one of our known physical venues
        source_is_physical = False
        physical_key = None
        for key in PHYSICAL_VENUES:
            if key.lower() in name.lower() or name.lower() in key.lower():
                source_is_physical = True
                physical_key = key
                break

        for i in range(num_events):
            days_away = random.randint(0, 10)

            # Generate a specific date based on days_away relative to actual dynamic base_date
            event_date = base_date + datetime.timedelta(days=days_away)
            event_date_str = event_date.strftime("%A, %B %d, %Y")

            # Categorize timeframe dynamically and correctly
            if days_away == 0:
                timeframe = "Today"
            elif event_date.weekday() in [4, 5, 6] and days_away <= (6 - today_weekday):
                timeframe = "This Weekend"
            elif days_away <= 7:
                timeframe = "Next 7 Days"
            else:
                timeframe = "Later"

            tag = random.choice(categories_pool)

            # Generate a time range
            start_hour = random.choice([8, 9, 10, 11, 12, 1, 2, 4, 6, 7, 8])
            start_min = random.choice(["00", "30"])
            meridiem = "AM" if start_hour in [8, 9, 10, 11] or start_hour == 12 else "PM"

            end_hour = (start_hour + random.choice([1, 2, 3])) % 12
            if end_hour == 0:
                end_hour = 12
            end_min = random.choice(["00", "30"])
            end_meridiem = "PM" if start_hour in [12, 1, 2, 4, 6, 7, 8] or (start_hour in [8, 9, 10, 11] and (start_hour + 3) >= 12) else "AM"

            time_range = f"{start_hour}:{start_min} {meridiem} – {end_hour}:{end_min} {end_meridiem}"

            cost = random.choice(["FREE", "FREE", "$5", "$10", "FREE"])

            # Specific titles per tag
            titles = {
                "Music": ["Acoustic Evening Concert", "Live Local Bands Showcase", "Jazz under the Stars", "Indie Rock Showcase"],
                "Theater": ["Comedy Night Live", "Shakespeare in the Park", "Improv Workshop", "Broadway Classics Concert"],
                "Family": ["Open Gym & Family Play", "Kids Storytime & Crafts", "Family Fun Festival", "Science Saturday Exploration"],
                "Outdoor": ["Guided Nature Walk", "Community Morning Yoga", "Sunset Bicycle Tour", "Farmer's Market & Crafts"],
                "Food & Drink": ["Trivia & Craft Beer Night", "Local Food Truck Rally", "Wine & Cheese Tasting", "Home Brewing Masterclass"],
                "Community": ["Town Hall Forum", "Community Volunteer Cleanup", "Local Artisan Fair", "Gainesville Tech Meetup"]
            }
            title_pool = titles.get(tag, ["Exciting Gathering"])
            title = f"{random.choice(title_pool)}"

            # Dynamically align content with the actual date and time
            actual_weekday_name = event_date.strftime("%A")
            title = title.replace("Saturday", actual_weekday_name)
            title = title.replace("Sunday", actual_weekday_name)
            title = title.replace("Monday", actual_weekday_name)
            title = title.replace("Tuesday", actual_weekday_name)
            title = title.replace("Wednesday", actual_weekday_name)
            title = title.replace("Thursday", actual_weekday_name)
            title = title.replace("Friday", actual_weekday_name)

            if meridiem == "PM" and "Morning" in title:
                title = title.replace("Morning", "Afternoon" if start_hour in [12, 1, 2, 3, 4] else "Evening")

            # Determine coordinates and address of the physical event host
            if source_is_physical:
                event_venue_name = physical_key
                event_lat = PHYSICAL_VENUES[physical_key]["lat"]
                event_lon = PHYSICAL_VENUES[physical_key]["lon"]
                event_address = PHYSICAL_VENUES[physical_key]["address"]
            else:
                # Choose from all physical venues randomly for online/media source events
                chosen_key = random.choice(list(PHYSICAL_VENUES.keys()))
                event_venue_name = chosen_key
                event_lat = PHYSICAL_VENUES[chosen_key]["lat"]
                event_lon = PHYSICAL_VENUES[chosen_key]["lon"]
                event_address = PHYSICAL_VENUES[chosen_key]["address"]

            venue_events.append({
                "title": title,
                "tag": tag.upper(),
                "timeframe": timeframe,
                "days_away": days_away,
                "date_str": event_date_str,
                "time_range": time_range,
                "cost": cost,
                "event_venue": event_venue_name,
                "event_lat": event_lat,
                "event_lon": event_lon,
                "event_address": event_address,
                "source_name": name,
                "description": f"Join us at {event_venue_name} for this incredible {tag.lower()} experience!"
            })
        # Sort by days away
        venue_events.sort(key=lambda x: x["days_away"])
        events[name] = venue_events
    return events

# Ensure we pass a standard Python tuple of strings, which is fully hashable by Streamlit
import datetime
today_str = datetime.date.today().isoformat()
mock_events = generate_mock_events(tuple(df["name"].unique()), today_str)

# --- Sidebar Controls ---
st.sidebar.header("Filter & Settings")

# 1. Search Bar (Search by venue name or event title)
search_query = st.sidebar.text_input("🔍 Search (Venue/Event)", "")

# 2. Category Selection
categories = sorted(df["category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "📂 Venue Categories",
    categories,
    default=categories
)

# 3. Time Slider (All, Next 7 Days, This Weekend, Today)
time_filter = st.sidebar.select_slider(
    "📅 Event Time Horizon",
    options=["All", "Next 7 Days", "This Weekend", "Today"]
)

# 4. Map View Toggle (Marker Cluster vs Heatmap)
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

# --- Filter Logic ---
# Gather all mock events across all sources and filter them dynamically
active_events = []
for source_name, events in mock_events.items():
    source_row = df[df["name"] == source_name]
    source_category = source_row.iloc[0]["category"] if not source_row.empty else "Other"

    for ev in events:
        phys_venue_name = ev["event_venue"]
        phys_venue_info = PHYSICAL_VENUES.get(phys_venue_name, {})
        phys_venue_cat = phys_venue_info.get("category", "Other")

        # 1. Category Filter
        if phys_venue_cat not in selected_categories:
            continue

        # 2. Search Query Filter
        if search_query:
            query = search_query.lower()
            match_venue = query in phys_venue_name.lower()
            match_title = query in ev["title"].lower()
            match_source = query in source_name.lower()
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
            # 0.036 degrees is roughly 2.5 miles
            dist = ((ev["event_lat"] - user_lat)**2 + (ev["event_lon"] - user_lon)**2)**0.5
            if dist > 0.036:
                continue

        # If we got here, the event is active!
        ev_copy = ev.copy()
        ev_copy["source_name"] = source_name
        active_events.append(ev_copy)

# Sort all active events chronologically by days_away
active_events.sort(key=lambda x: x["days_away"])

# Group active events by their physical hosting venue
events_by_physical_venue = {}
for ev in active_events:
    venue_name = ev["event_venue"]
    if venue_name not in events_by_physical_venue:
        events_by_physical_venue[venue_name] = []
    events_by_physical_venue[venue_name].append(ev)

# Create a summary of active physical venues for metrics and drop-downs
active_venues_data = []
for name, v_events in events_by_physical_venue.items():
    v_info = PHYSICAL_VENUES.get(name, {
        "address": "Gainesville, FL",
        "lat": 29.6516,
        "lon": -82.3248,
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
        "description": f"Physical hosting venue located at {v_info['address']}."
    })
filtered = pd.DataFrame(active_venues_data) if active_venues_data else pd.DataFrame(columns=["name", "category", "lat", "lon", "website", "address", "description"])

# --- Initialize Session State for Active Venue (st_folium hook integration) ---
if "selected_venue" not in st.session_state:
    active_physical_venue_names = sorted(list(events_by_physical_venue.keys())) if events_by_physical_venue else sorted(list(PHYSICAL_VENUES.keys()))
    st.session_state["selected_venue"] = active_physical_venue_names[0]

# --- Metrics section ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Venues Selected", len(filtered))
with col2:
    st.metric("Total Match Events Found", len(active_events))
with col3:
    st.metric("Active Categories", len(filtered["category"].unique()) if len(filtered) > 0 else 0)

# --- Build Folium Map ---
colors_mapping = {
    "Music": "blue",
    "Arts": "purple",
    "Museum": "green",
    "Library": "orange",
    "Park": "darkgreen",
    "Sports": "cadetblue",
    "University": "black",
    "Brewery": "red",
    "Other": "gray"
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

# Base location for Map: center of Gainesville
m = folium.Map(
    location=[29.6516, -82.3248],
    zoom_start=13,
    tiles="CartoDB positron"
)

# User "Near Me" simulation pinpoint
if near_me_enabled:
    folium.Marker(
        [user_lat, user_lon],
        popup="<b>You are here (Simulated)</b>",
        tooltip="Your Location",
        icon=folium.Icon(color="red", icon="user", prefix="fa")
    ).add_to(m)

# Apply Map rendering mode
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
        emoji = emojis_mapping.get(cat, "📍")

        # Directions link to Google Maps
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

        desc_html = f'<p style="font-size: 0.85rem; color: #4B5563; margin: 8px 0 4px 0;"><i>{desc}</i></p>'

        events_html = ""
        if v_events:
            events_html += '<div style="border-top: 1px solid #E5E7EB; margin-top: 10px; padding-top: 10px; font-family: \'Helvetica Neue\', Arial, sans-serif; line-height: 1.4; max-height: 180px; overflow-y: auto;">'
            events_html += f'<div style="font-weight: bold; font-size: 0.9rem; color: #374151; margin-bottom: 6px;">Upcoming Events ({len(v_events)}):</div>'
            for ev in v_events[:3]:
                events_html += f"""
                <div style="margin-bottom: 8px; border-bottom: 1px dashed #F3F4F6; padding-bottom: 6px;">
                    <div style="font-weight: bold; font-size: 0.85rem; color: #1F2937; margin-bottom: 2px;">{ev['title']}</div>
                    <div style="color: #4B5563; font-size: 0.8rem; margin-bottom: 2px;">{ev['date_str']}, {ev['time_range']}</div>
                    <div style="color: #4B5563; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 2px;">{ev['tag']} · <span style="color: #059669;">{ev['cost']}</span></div>
                    <div style="color: #2563EB; font-size: 0.75rem;">Source: {ev['source_name']}</div>
                </div>
                """
            if len(v_events) > 3:
                events_html += f'<div style="font-size: 0.75rem; color: #6B7280; text-align: center;">+ {len(v_events) - 3} more events (see below)</div>'
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

        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=name,
            icon=folium.Icon(
                color=colors_mapping.get(cat, "gray"),
                icon="info-sign"
            )
        ).add_to(cluster)
else:
    # Heatmap mode
    heat_data = []
    for _, row in filtered.iterrows():
        name = row["name"]
        v_events = events_by_physical_venue.get(name, [])
        heat_data.append([row["lat"], row["lon"], float(len(v_events))])
    if heat_data:
        HeatMap(heat_data, radius=25, blur=15).add_to(m)

# Render map in Streamlit and capture interactive st_folium return hook
map_data = st_folium(
    m,
    use_container_width=True,
    height=550,
    key="gainesville_map"
)

# --- Bidirectional Streamlit Event Hook / Click Handler ---
# When a marker is clicked on standard map view, update the session_state selected_venue!
if map_data and map_data.get("last_object_clicked_tooltip"):
    clicked_venue = map_data["last_object_clicked_tooltip"]
    # Check if clicked venue exists in current filter set
    if clicked_venue in filtered["name"].values:
        st.session_state["selected_venue"] = clicked_venue

# --- Click Interaction / Venue Details Sidebar & Tabbed Schedules ---
st.markdown("---")
st.subheader("🗓️ Venue Explorer & Full Schedule")

if len(filtered) == 0:
    st.warning("No physical venues found matching the current filters.")
else:
    # Tabbed interface
    tab1, tab2 = st.tabs(["📅 Full Schedule (All Selected Venues)", "📍 Individual Venue Explorer"])

    with tab1:
        st.markdown(f"**Showing all {len(active_events)} events across all {len(filtered)} active physical venues matching the \"{time_filter}\" horizon.**")
        if not active_events:
            st.info("No events scheduled across any of the selected venues in this time horizon.")
        else:
            for ev in active_events:
                ev_directions_url = f"https://www.google.com/maps/dir/?api=1&destination={ev['event_lat']},{ev['event_lon']}"
                st.markdown(f"""
                <div style="background-color: #F9FAFB; border-left: 4px solid #1E3A8A; padding: 12px; margin-bottom: 12px; border-radius: 0 4px 4px 0; font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.5;">
                    <div style="font-weight: bold; font-size: 1.05rem; color: #1F2937; margin-bottom: 2px;">{ev['title']}</div>
                    <div style="color: #4B5563; font-size: 0.9rem; margin-bottom: 4px;">{ev['date_str']}, {ev['time_range']} · <b>{ev['event_venue']}</b></div>
                    <div style="color: #4B5563; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 2px;">{ev['tag']} · <a href="{ev_directions_url}" target="_blank" style="color: #059669; text-decoration: none;">🚗 Directions to Event Venue</a></div>
                    <div style="color: #059669; font-weight: bold; font-size: 0.8rem; margin-bottom: 2px;">{ev['cost']}</div>
                    <div style="color: #2563EB; font-size: 0.85rem; font-weight: 500;">Calendar Source: {ev['source_name']}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        # Ensure current state venue is valid with current filters, else fallback
        venue_list = sorted(filtered["name"].unique()) if not filtered.empty else sorted(list(PHYSICAL_VENUES.keys()))
        current_selected = st.session_state["selected_venue"]
        if current_selected not in venue_list:
            current_selected = venue_list[0]
            st.session_state["selected_venue"] = current_selected

        # Interactive dropdown to manually change venue or view updated state hook selection
        selected_venue_idx = venue_list.index(current_selected)

        selected_venue_name = st.selectbox(
            "Select a venue to inspect its upcoming events:",
            venue_list,
            index=selected_venue_idx,
            key="venue_selectbox"
        )
        # Save manually updated option back to state
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
                    for ev in venue_events:
                        ev_directions_url = f"https://www.google.com/maps/dir/?api=1&destination={ev['event_lat']},{ev['event_lon']}"
                        st.markdown(f"""
                        <div style="background-color: #F9FAFB; border-left: 4px solid #3B82F6; padding: 12px; margin-bottom: 12px; border-radius: 0 4px 4px 0; font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.5;">
                            <div style="font-weight: bold; font-size: 1.05rem; color: #1F2937; margin-bottom: 2px;">{ev['title']}</div>
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
