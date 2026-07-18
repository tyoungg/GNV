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
    # Resolve the path relative to the current file to support running from any directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "venues.csv")
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
@st.cache_data
def generate_mock_events(venue_names):
    random.seed(42)  # For consistent results
    categories_pool = ["Music", "Theater", "Family", "Outdoor", "Food & Drink", "Community"]
    events = {}

    for name in venue_names:
        num_events = random.randint(1, 15)
        venue_events = []
        for i in range(num_events):
            days_away = random.randint(0, 10)
            if days_away == 0:
                timeframe = "Today"
            elif days_away <= 2:
                timeframe = "This Weekend"
            else:
                timeframe = "Next 7 Days"

            tag = random.choice(categories_pool)
            venue_events.append({
                "title": f"Exciting {tag} Gathering {i+1}",
                "tag": tag,
                "timeframe": timeframe,
                "days_away": days_away,
                "description": f"Join us at {name} for this incredible {tag.lower()} experience!"
            })
        # Sort by days away
        venue_events.sort(key=lambda x: x["days_away"])
        events[name] = venue_events
    return events

mock_events = generate_mock_events(df["name"].unique())

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

# 3. Time Slider (Today, This Weekend, Next 7 Days)
time_filter = st.sidebar.select_slider(
    "📅 Event Time Horizon",
    options=["All", "Today", "This Weekend", "Next 7 Days"]
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

        events = mock_events.get(name, [])
        emoji = emojis_mapping.get(cat, "📍")

        # Directions link to Google Maps
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

        popup_html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 5px 0; color: #1E3A8A;">{emoji} {name}</h4>
            <span style="background-color: #F3F4F6; color: #374151; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">{cat} Venue</span>
            <p style="font-size: 0.9rem; margin: 10px 0;"><b>Upcoming events:</b> {len(events)}</p>
            <div style="margin-top: 10px;">
                <a href="{url}" target="_blank" style="background-color: #2563EB; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 0.8rem; margin-right: 5px;">Website</a>
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
                <div style="background-color: #F9FAFB; border-left: 4px solid #3B82F6; padding: 10px; margin-bottom: 10px; border-radius: 0 4px 4px 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold; color: #1F2937;">{ev['title']}</span>
                        <span style="background-color: #E0E7FF; color: #4338CA; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">{ev['timeframe']}</span>
                    </div>
                    <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: #4B5563;">{ev['description']}</p>
                    <span style="font-size: 0.75rem; color: #9CA3AF;">Tag: {ev['tag']}</span>
                </div>
                """, unsafe_allow_html=True)
