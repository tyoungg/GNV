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

            venue_events.append({
                "title": title,
                "tag": tag.upper(),
                "timeframe": timeframe,
                "days_away": days_away,
                "date_str": event_date_str,
                "time_range": time_range,
                "cost": cost,
                "description": f"Join us at {name} for this incredible {tag.lower()} experience!"
            })
        # Sort by days away
        venue_events.sort(key=lambda x: x["days_away"])
        events[name] = venue_events
    return events

# Ensure we pass a standard Python tuple of strings, which is fully hashable by Streamlit
import datetime
today_str = datetime.date.today().isoformat()
mock_events = generate_mock_events(tuple(df["name"].unique()), today_str)

# --- Initialize Session State for Active Venue (st_folium hook integration) ---
if "selected_venue" not in st.session_state:
    st.session_state["selected_venue"] = sorted(df["name"].unique())[0]

# --- Sidebar Controls ---
st.sidebar.header("Filter & Settings")

# 1. Search Bar (Search by venue name)
search_query = st.sidebar.text_input("🔍 Search Venue Name", "")

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
# Filter by categories first
filtered = df[df.category.isin(selected_categories)]

# Filter by Search Query
if search_query:
    filtered = filtered[filtered["name"].str.contains(search_query, case=False)]

# Filter based on "Near Me" proximity (rough distance calculation)
if near_me_enabled:
    # 0.036 degrees is roughly 2.5 miles
    filtered = filtered[
        ((filtered["lat"] - user_lat)**2 + (filtered["lon"] - user_lon)**2)**0.5 <= 0.036
    ]

# Filter based on Time Horizon matching the mock events
if time_filter != "All":
    matching_venues = []
    for name in filtered["name"]:
        events = mock_events.get(name, [])
        if time_filter == "Today" and any(e["timeframe"] == "Today" for e in events):
            matching_venues.append(name)
        elif time_filter == "This Weekend" and any(e["timeframe"] in ["Today", "This Weekend"] for e in events):
            matching_venues.append(name)
        elif time_filter == "Next 7 Days" and any(e["timeframe"] in ["Today", "This Weekend", "Next 7 Days"] for e in events):
            matching_venues.append(name)
    filtered = filtered[filtered["name"].isin(matching_venues)]

# --- Metrics section ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Venues Selected", len(filtered))
with col2:
    total_events = sum(len(mock_events.get(name, [])) for name in filtered["name"])
    st.metric("Total Match Events Found", total_events)
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
        desc = row.get("description", "") if "description" in row else ""
        date_added = row.get("date_added", "2026-07-14") if "date_added" in row else "2026-07-14"

        events = mock_events.get(name, [])
        emoji = emojis_mapping.get(cat, "📍")

        # Directions link to Google Maps
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

        desc_html = f'<p style="font-size: 0.85rem; color: #4B5563; margin: 8px 0 4px 0;"><i>{desc}</i></p>' if desc and str(desc) != "nan" else ""

        first_event_html = ""
        if events:
            ev = events[0]
            first_event_html = f"""
            <div style="border-top: 1px solid #E5E7EB; margin-top: 10px; padding-top: 10px; font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.4;">
                <div style="font-weight: bold; font-size: 0.95rem; color: #1F2937; margin-bottom: 2px;">{ev['title']}</div>
                <div style="color: #4B5563; font-size: 0.85rem; margin-bottom: 4px;">{ev['date_str']}, {ev['time_range']} · {name}</div>
                <div style="color: #4B5563; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 2px;">{ev['tag']}</div>
                <div style="color: #059669; font-weight: bold; font-size: 0.75rem; margin-bottom: 2px;">{ev['cost']}</div>
                <div style="color: #2563EB; font-size: 0.8rem; font-weight: 500;">{name}</div>
            </div>
            """

        popup_html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 5px 0; color: #1E3A8A;">{emoji} {name}</h4>
            <span style="background-color: #F3F4F6; color: #374151; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">{cat} Venue</span>
            {desc_html}
            {first_event_html}
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
    heat_data = [[row["lat"], row["lon"], 1.0] for _, row in filtered.iterrows()]
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

# --- Click Interaction / Venue Details Sidebar ---
st.markdown("---")
st.subheader("🗓️ Venue Details & Events List")

if len(filtered) == 0:
    st.warning("No venues found matching the current filters.")
else:
    # Ensure current state venue is valid with current filters, else fallback
    venue_list = sorted(filtered["name"].unique())
    current_selected = st.session_state["selected_venue"]
    if current_selected not in venue_list:
        current_selected = venue_list[0]
        st.session_state["selected_venue"] = current_selected

    # Interactive dropdown to manually change venue or view updated state hook selection
    selected_venue_idx = venue_list.index(current_selected)

    selected_venue_name = st.selectbox(
        "Select a venue to inspect its upcoming events:",
        venue_list,
        index=selected_venue_idx
    )
    # Save manually updated option back to state
    st.session_state["selected_venue"] = selected_venue_name

    venue_data = filtered[filtered["name"] == selected_venue_name].iloc[0]
    st.markdown(f"### {emojis_mapping.get(venue_data['category'], '📍')} {venue_data['name']}")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**Category:** {venue_data['category']}")
        st.markdown(f"**Website:** [Visit Official Website]({venue_data['website']})")
        if "date_added" in venue_data and str(venue_data["date_added"]) != "nan":
            st.markdown(f"📅 **Added to map:** {venue_data['date_added']}")
        directions_link = f"https://www.google.com/maps/dir/?api=1&destination={venue_data['lat']},{venue_data['lon']}"
        st.markdown(f"🚗 [Get Google Maps Directions]({directions_link})")

    with col2:
        st.markdown("**Upcoming Events Schedule:**")
        events = mock_events.get(selected_venue_name, [])
        if not events:
            st.write("No events scheduled for this venue in the selected time horizon.")
        else:
            for ev in events:
                # Filter events based on time slide filter
                if time_filter == "Today" and ev["timeframe"] != "Today":
                    continue
                if time_filter == "This Weekend" and ev["timeframe"] not in ["Today", "This Weekend"]:
                    continue
                if time_filter == "Next 7 Days" and ev["timeframe"] not in ["Today", "This Weekend", "Next 7 Days"]:
                    continue

                st.markdown(f"""
                <div style="background-color: #F9FAFB; border-left: 4px solid #3B82F6; padding: 12px; margin-bottom: 12px; border-radius: 0 4px 4px 0; font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.5;">
                    <div style="font-weight: bold; font-size: 1.05rem; color: #1F2937; margin-bottom: 2px;">{ev['title']}</div>
                    <div style="color: #4B5563; font-size: 0.9rem; margin-bottom: 4px;">{ev['date_str']}, {ev['time_range']} · {selected_venue_name}</div>
                    <div style="color: #4B5563; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 2px;">{ev['tag']}</div>
                    <div style="color: #059669; font-weight: bold; font-size: 0.8rem; margin-bottom: 2px;">{ev['cost']}</div>
                    <div style="color: #2563EB; font-size: 0.85rem; font-weight: 500;">{selected_venue_name}</div>
                </div>
                """, unsafe_allow_html=True)
