import os
import pandas as pd
from scraper import scrape_sources
from geocode import geocode_venue

def run_ingestion_pipeline():
    """
    Runs the full scraping and geocoding pipeline.
    It scrapes the sources, checks with existing cached data in data/venues.csv,
    geocodes new or updated venues, and updates the CSV.
    """
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "venues.csv")

    # 1. Load existing cache if exists
    if os.path.exists(csv_path):
        print(f"Loading existing venue cache from {csv_path}...")
        df_existing = pd.read_csv(csv_path)
    else:
        print("No existing venue CSV found. Starting fresh.")
        df_existing = pd.DataFrame(columns=["name", "category", "lat", "lon", "website"])

    # Convert existing names to lower for easy comparison
    existing_lookup = {}
    for _, row in df_existing.iterrows():
        existing_lookup[row["name"].lower().strip()] = {
            "category": row["category"],
            "lat": row["lat"],
            "lon": row["lon"],
            "website": row["website"]
        }

    # 2. Scrape live sources
    print("Scraping live sources page...")
    scraped_venues = scrape_sources()
    print(f"Scraped {len(scraped_venues)} sources from Gainesville Events.")

    # 3. Process, merge, and geocode new venues
    updated_rows = []

    for v in scraped_venues:
        name = v["name"]
        clean_name = name.lower().strip()
        category = v["category"]
        website = v["website"]

        # If already cached, we reuse existing geocoded latitude/longitude
        if clean_name in existing_lookup:
            cached = existing_lookup[clean_name]
            lat = cached["lat"]
            lon = cached["lon"]
            # Keep original category if scraped category is Other
            cat = category if category != "Other" else cached["category"]
        else:
            print(f"New venue discovered: '{name}'. Geocoding...")
            lat, lon = geocode_venue(name)
            cat = category

        updated_rows.append({
            "name": name,
            "category": cat,
            "lat": lat,
            "lon": lon,
            "website": website
        })

    # Ensure some essential core manual venues are included if they got missed/filtered
    core_manual_venues = [
        {"name": "Heartwood Soundstage", "category": "Music", "lat": 29.645, "lon": -82.324, "website": "https://heartwoodsoundstage.com"},
        {"name": "High Dive", "category": "Music", "lat": 29.652, "lon": -82.324, "website": "https://highdivegville.com"},
        {"name": "Depot Park", "category": "Park", "lat": 29.644, "lon": -82.317, "website": "https://www.gainesvillefl.gov"},
        {"name": "Cade Museum", "category": "Museum", "lat": 29.644, "lon": -82.316, "website": "https://cademuseum.org"},
        {"name": "Florida Museum of Natural History", "category": "Museum", "lat": 29.638, "lon": -82.369, "website": "https://www.floridamuseum.ufl.edu"}
    ]

    for cm in core_manual_venues:
        # Check if already present in updated_rows
        present = False
        for r in updated_rows:
            if r["name"].lower().strip() == cm["name"].lower().strip():
                present = True
                break
        if not present:
            updated_rows.append(cm)

    # 4. Save back to CSV
    df_updated = pd.DataFrame(updated_rows)
    # Deduplicate in case
    df_updated = df_updated.drop_duplicates(subset=["name"])

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df_updated.to_csv(csv_path, index=False)
    print(f"Saved {len(df_updated)} venues to {csv_path}.")

if __name__ == "__main__":
    run_ingestion_pipeline()
