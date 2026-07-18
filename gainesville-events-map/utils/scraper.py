import requests
from bs4 import BeautifulSoup
import re

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
