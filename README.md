# 🗺️ Gainesville Events Map

A self-contained interactive Streamlit application that scrapes, geocodes, and maps local calendar sources feeding [GainesvilleEvents.com](https://gainesvilleevents.com/sources/). It serves as an intuitive portal for discovering where events originate in Gainesville and Alachua County.

Please find the complete self-contained Streamlit project inside the [gainesville-events-map/](./gainesville-events-map/) directory.

---

## 🚀 Features

- **Interactive Folium Map:** Switch dynamically between standard **Pin Cluster** and **Density Heatmaps**.
- **Source Scraping & Automated Ingestion:** Live scraper retrieves sources from `gainesvilleevents.com/sources/`, caches results, and maps them efficiently.
- **Enhanced Search & Filters:** Search for venues by name, filter by multiple categories, or adjust the **Event Time Horizon** (Today, This Weekend, Next 7 Days).
- **Simulated "Near Me" GPS Location:** Filter to show only venues within a 2.5-mile radius of downtown Gainesville.
- **Rich Popup Cards & Directions:** Map markers display beautiful UI cards with category tags, mock upcoming event counts, website links, and direct **Google Maps Directions** hyperlinks.
- **Detailed Schedules Panel:** Expand any venue to view simulated schedules and descriptions of upcoming events.

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
└── README.md                # Project documentation
```

---

## 🛠️ Quick Start

### 1. Install Dependencies
Make sure you have Python 3.10+ installed. Install the required Python packages:

```bash
pip install -r gainesville-events-map/requirements.txt
```

### 2. Run the Ingestion Pipeline (Optional)
To fetch fresh data, scrape the website, resolve coords, and update the cache:

```bash
python3 gainesville-events-map/utils/run_pipeline.py
```

### 3. Start the Streamlit App
Launch the web application locally:

```bash
streamlit run gainesville-events-map/app.py
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
          pip install -r gainesville-events-map/requirements.txt
      - name: Run Pipeline
        run: |
          python gainesville-events-map/utils/run_pipeline.py
      - name: Commit & Push Changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "chore: auto-update venues cache"
          file_pattern: "gainesville-events-map/data/venues.csv"
```
