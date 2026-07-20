# 🗺️ Gainesville Events & Venues Map

An interactive Streamlit application that scrapes, geocodes, and dynamically maps over **30+ local calendar sources** feeding [GainesvilleEvents.com/sources](https://gainesvilleevents.com/sources/).

Rather than plotting general website or administrative headquarters on the map, this application **groups, schedules, and maps all upcoming events to their precise, actual physical hosting locations** across Gainesville and Alachua County!

---

## 🚀 Features

- **Interactive Physical Venue Mapping:** Events are grouped and plotted on their actual physical venues using precise coordinate resolution and caches.
- **Dynamic Event Count Badges:** Map markers display beautiful circular badges with the number of upcoming events scheduled at each physical location.
- **Pulsing Today Visual Indicator:** Venues hosting at least one active event scheduled for **Today** display a glowing pulsing red ring animation to attract attention.
- **Vibrant Interactive Sidebar Legend:** A custom-styled visual guide showcasing the dynamic event categories (Music, Arts, Museum, Library, Sports, Parks, etc.) and color mapping.
- **30+ Live Scraped Calendar Sources:** Automatically crawls, normalizes, and deduplicates the comprehensive registry of event feeds from [GainesvilleEvents.com/sources](https://gainesvilleevents.com/sources/).
- **Interactive Folium Map:** Switch dynamically between standard **Pin Cluster** and **Density Heatmaps**.
- **Enhanced Search & Filters:** Search for venues by name, filter by multiple categories, or adjust the **Event Time Horizon** (Today, This Weekend, Next 7 Days, All).
- **Simulated "Near Me" GPS Location:** Filter to show only venues within a 2.5-mile radius of downtown Gainesville.
- **Rich Popup Cards & Directions:** Map markers display beautiful UI cards with category tags, mock upcoming event counts, website links, and direct **Google Maps Directions** hyperlinks.
- **Detailed Schedules Panel:** Expand any physical venue to view simulated schedules and descriptions of upcoming events.

---

## 📂 Project Structure

```
gainesville-events-map/
│
├── app.py                   # Main interactive Streamlit application
├── requirements.txt         # Core dependencies
│
├── .streamlit/
│   └── config.toml          # Custom theme configuration
│
├── data/
│   └── venues.csv           # Cached geocoded venues
│
├── utils/
│   ├── geocode.py           # Geocoding module with predefined fallbacks & cache
│   ├── scraper.py           # Web scraper for the live Gainesville Events Sources page
│   └── run_pipeline.py      # Main script to run the update data pipeline
│
└── README.md                # Documentation (this file)
```

---

## 🛠️ Quick Start

### 1. Install Dependencies
Make sure you have Python 3.10+ installed. Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Run the Ingestion Pipeline (Optional)
To fetch fresh data, scrape the website, resolve coords, and update the cache:

```bash
python3 utils/run_pipeline.py
```

### 3. Start the Streamlit App
Launch the web application locally:

```bash
streamlit run app.py
```

---

## 🤖 Automating Updates with GitHub Actions
You can keep the list of venues self-maintaining with a nightly GitHub Action. Add a file under `.github/workflows/refresh-venues.yml`:

```yaml
name: Refresh Venues Cache

on:
  schedule:
    - cron: '0 0 * * *' # Run nightly
  workflow_dispatch:

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run Pipeline
        run: |
          python utils/run_pipeline.py
      - name: Commit & Push Changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "chore: auto-update venues cache"
          file_pattern: "data/venues.csv"
```
