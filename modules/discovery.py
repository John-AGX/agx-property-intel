"""
AGX Property Intelligence — Property Discovery Module

Uses Google Places API to find large multifamily apartment complexes
across Central Florida.
"""

import urllib.request
import urllib.parse
import json
import time
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from config import SEARCH_AREAS, SEARCH_QUERIES, MIN_REVIEWS, MAX_STAR_RATING, API_DELAY


def api_get(url):
    """Make a GET request and return parsed JSON."""
    req = urllib.request.Request(url, headers={"User-Agent": "AGX-PropertyIntel/2.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_places(query, lat, lng, radius, api_key):
    """Search for places using Google Places Text Search API."""
    base = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = urllib.parse.urlencode({
        "query": query,
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "establishment",
        "key": api_key,
    })
    results = []
    url = f"{base}?{params}"

    while url:
        data = api_get(url)
        results.extend(data.get("results", []))
        token = data.get("next_page_token")
        if token:
            time.sleep(2)
            url = f"{base}?pagetoken={token}&key={api_key}"
        else:
            url = None

    return results


def get_place_details(place_id, api_key):
    """Get detailed info including reviews for a place."""
    base = "https://maps.googleapis.com/maps/api/place/details/json"
    params = urllib.parse.urlencode({
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,rating,"
                  "user_ratings_total,reviews,url,business_status,address_components",
        "key": api_key,
    })
    data = api_get(f"{base}?{params}")
    return data.get("result", {})


def detect_county(address, address_components=None):
    """Try to detect which county a property is in based on address."""
    address_lower = address.lower()

    if address_components:
        for comp in address_components:
            if "administrative_area_level_2" in comp.get("types", []):
                county_name = comp.get("long_name", "").lower().replace(" county", "")
                if county_name in ["orange", "seminole", "osceola", "polk", "brevard", "volusia", "lake"]:
                    return county_name

    city_county_map = {
        "orlando": "orange", "winter park": "orange", "apopka": "orange", "maitland": "orange",
        "sanford": "seminole", "altamonte": "seminole", "casselberry": "seminole", "longwood": "seminole",
        "kissimmee": "osceola", "st. cloud": "osceola", "celebration": "osceola",
        "lakeland": "polk", "winter haven": "polk", "bartow": "polk", "haines city": "polk",
        "melbourne": "brevard", "palm bay": "brevard", "cocoa": "brevard", "titusville": "brevard",
        "daytona": "volusia", "deltona": "volusia", "port orange": "volusia", "deland": "volusia",
        "clermont": "lake", "leesburg": "lake", "eustis": "lake", "tavares": "lake",
    }
    for city, county in city_county_map.items():
        if city in address_lower:
            return county

    return "unknown"


def discover_properties(api_key, db, areas=None, queries=None):
    if not api_key:
        print("  ⚠️  No Google Places API key — skipping discovery")
        return 0

    areas = areas or SEARCH_AREAS
    queries = queries or SEARCH_QUERIES

    print("\n" + "=" * 60)
    print("  MODULE 1: Property Discovery (Google Places)")
    print("=" * 60)

    all_places = {}

    for area in areas:
        for query in queries:
            print(f"  🔍 '{query}' near {area['name']}...")
            try:
                results = search_places(query, area["lat"], area["lng"], area["radius"], api_key)
                for place in results:
                    pid = place.get("place_id")
                    total = place.get("user_ratings_total", 0)
                    rating = place.get("rating", 5)

                    if pid and total >= MIN_REVIEWS and rating <= MAX_STAR_RATING:
                        if pid not in all_places:
                            all_places[pid] = {
                                "place_id": pid,
                                "name": place.get("name", "Unknown"),
                                "address": place.get("formatted_address", ""),
                                "rating": rating,
                                "total_reviews": total,
                                "search_area": area["name"],
                                "county_hint": area.get("county", ""),
                            }

                time.sleep(API_DELAY)
            except Exception as e:
                print(f"    ⚠ Error: {e}")
                continue

    print(f"\n  Found {len(all_places)} apartment complexes meeting criteria.")
    print(f"  Fetching details and storing...\n")

    new_count = 0
    for i, (pid, info) in enumerate(all_places.items(), 1):
        print(f"  [{i}/{len(all_places)}] {info['name']}...")

        try:
            details = get_place_details(pid, api_key)
            address = details.get("formatted_address", info["address"])
            county = detect_county(address, details.get("address_components"))
            if county == "unknown":
                county = info.get("county_hint", "unknown")

            existing = db.get(address)
            if existing:
                db.upsert(address, {
                    "google_rating": details.get("rating", info["rating"]),
                    "total_reviews": details.get("user_ratings_total", info["total_reviews"]),
                    "phone": details.get("formatted_phone_number", ""),
                    "website": details.get("website", ""),
                    "google_url": details.get("url", ""),
                })
                print(f"    ↛ Updated existing property")
            else:
                profile = db.new_property_template(
                    name=details.get("name", info["name"]),
                    address=address,
                    county=county,
                )
                profile.update({
                    "place_id": pid,
                    "google_url": details.get("url", ""),
                    "phone": details.get("formatted_phone_number", ""),
                    "website": details.get("website", ""),
                    "google_rating": details.get("rating", info["rating"]),
                    "total_reviews": details.get("user_ratings_total", info["total_reviews"]),
                })
                db.upsert(address, profile)
                new_count += 1
                print(f"    ✓ New property added ({county})")

            reviews = details.get("reviews", [])
            if reviews:
                db.upsert(address, {"_raw_reviews": reviews})

            time.sleep(API_DELAY)
        except Exception as e:
            print(f"    ⚠ Error: {e}")
            continue

    print(f"\n  ✅ Discovery complete: {new_count} new, {len(all_places) - new_count} updated")
    return new_count
