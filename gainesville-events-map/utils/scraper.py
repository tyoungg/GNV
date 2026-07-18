import requests
from bs4 import BeautifulSoup
import re

def normalize_name(name: str) -> str:
    """
    Normalizes venue names to consolidate duplicates, strip out common suffixes/phrases,
    and ensure a clean, standardized format.
    """
    # Clean up excess spaces first
    name = re.sub(r'\s+', ' ', name).strip()
    name_lower = name.lower()

    # 1. Check exact/keyword matches for known venues to prevent over-stripping
    overrides = {
        "gainesville events facebook page": "Gainesville Events",
        "gainesville community events and activities": "Gainesville Community Events",
        "gainesville community events": "Gainesville Community Events",
        "gainesville events directory": "City of Gainesville",
        "gainesville events": "Gainesville Events",
        "alachua county meetings & events": "Alachua County Meetings & Events",
        "visit gainesville festivals & special events": "Visit Gainesville",
        "visit gainesville events": "Visit Gainesville",
        "visit gainesville": "Visit Gainesville",
        "things to do gainesville group": "Things To Do Gainesville",
        "things to do gainesville": "Things To Do Gainesville",
        "greater gainesville chamber community events": "Greater Gainesville Chamber",
        "greater gainesville chamber": "Greater Gainesville Chamber",
        "celebration pointe events": "Celebration Pointe",
        "celebration pointe": "Celebration Pointe",
        "depot park events calendar": "Depot Park",
        "depot park": "Depot Park",
        "high dive": "High Dive",
        "heartwood": "Heartwood Soundstage",
    }

    for key, val in overrides.items():
        if key in name_lower:
            return val

    # 2. General suffix removal for other/new venues
    # Remove any parenthetical comments first (e.g., "(alt URL)")
    name = re.sub(r'\s*\(.*?\)', '', name)

    suffixes = [
        " Festivals & Special Events",
        " Events Calendar",
        " Events Directory",
        " Community Update",
        " Facebook Page",
        " Facebook Group",
        " Directory",
        " Calendar",
        " Events",
        " Event",
        " Group",
    ]

    # Sort suffixes by length descending to match longest first
    for suffix in sorted(suffixes, key=len, reverse=True):
        if name.lower().endswith(suffix.lower()):
            name = name[:-len(suffix)]

    # Clean up trailing punctuation or leftover characters (e.g., &, -, :, comma)
    name = re.sub(r'[\s\-\&,:\.]+$', '', name).strip()
    return re.sub(r'\s+', ' ', name).strip()


def scrape_sources():
    """
    Scrapes the Gainesville Events Sources page to retrieve venue listings,
    their website URLs, categories, and any extra descriptive details.
    """
    url = "https://gainesvilleevents.com/sources/"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    venues = []

    # Map keywords/names to typical categories for better initial assignment
    category_mapping = {
        "museum": "Museum",
        "harn": "Museum",
        "cade": "Museum",
        "florida museum": "Museum",
        "library": "Library",
        "gators": "Sports",
        "performing arts": "Arts",
        "theatre": "Arts",
        "hippodrome": "Arts",
        "depot park": "Park",
        "heartwood": "Music",
        "high dive": "Music",
        "shows": "Music",
        "glory days": "Music",
        "brewery": "Brewery",
        "beer": "Brewery",
        "celebration pointe": "Other",
        "chamber": "Other",
        "gainesville events": "Other",
        "high springs": "Other",
        "city of alachua": "Other",
        "santa fe college": "University",
        "uf": "University",
    }

    # Find the sources. Typically, these are inside list items (li) within the live sources or directory sections.
    # Looking at the raw parsed text from before, they are in lists under headings.
    for li in soup.find_all("li"):
        a = li.find("a")
        if not a:
            continue

        name = a.get_text(strip=True)
        website = a.get("href", "").strip()

        # Filter out navigation links, standard header/footer links
        if not website or website.startswith("/") or "gainesvilleevents.com" in website:
            if not website.endswith("feed.ics"):
                continue

        # Clean up names (remove trailing characters or clean whitespaces)
        name = re.sub(r'\s+', ' ', name).strip()

        # Normalize names to consolidate duplicate/varied entries
        name = normalize_name(name)

        # Determine category based on name keywords
        category = "Other"
        for keyword, cat in category_mapping.items():
            if keyword in name.lower() or keyword in website.lower():
                category = cat
                break

        # Extract address description or extra text from list item if available
        # e.g., "Cade Museum - The Events Calendar REST API"
        description = li.get_text(strip=True)
        description = description.replace(name, "").strip()
        # Clean up description prefix/suffix
        description = re.sub(r'^\s*[-·•:*]\s*', '', description)

        venues.append({
            "name": name,
            "category": category,
            "website": website,
            "description": description
        })

    # Let's deduplicate based on website and name to keep it clean
    unique_venues = []
    seen = set()
    for venue in venues:
        key = (venue["name"].lower(), venue["website"].lower())
        if key not in seen:
            seen.add(key)
            unique_venues.append(venue)

    return unique_venues

if __name__ == "__main__":
    print("Scraping Gainesville Events sources...")
    results = scrape_sources()
    print(f"Successfully scraped {len(results)} sources:")
    for idx, r in enumerate(results[:10]):
        print(f"[{idx+1}] Name: {r['name']} | Cat: {r['category']} | URL: {r['website']}")
