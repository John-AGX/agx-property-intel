"""
AGX Property Intelligence — Permit Scraper Module

Scrapes county building permit databases to find:
- Last roof permit (when was the roof last replaced/repaired?)
- Last paint/exterior permit
- Last structural work
- Any recent large permits

Supports two modes:
1. FREE: Selenium browser automation for each county portal
2. PAID: Shovels.ai API (set SHOVELS_API_KEY in config)

Most FL counties use Accela Citizen Access — the scrapers handle
the JavaScript-heavy interfaces via Selenium WebDriver.
"""

import re
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    COUNTIES, PERMIT_CATEGORIES, SHOVELS_API_KEY,
    SELENIUM_TIMEOUT, ROOF_AGE_ALERT_YEARS, PAINT_AGE_ALERT_YEARS,
)

# Try to import Selenium (optional — only needed for free scraping)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def categorize_permit(description):
    """Categorize a permit based on its description text."""
    desc_lower = description.lower()
    for cat_name, cat_config in PERMIT_CATEGORIES.items():
        for keyword in cat_config["keywords"]:
            if keyword.lower() in desc_lower:
                return cat_name, cat_config["priority"]
    return "other", "low"


def parse_date(date_str):
    """Try to parse various date formats from permit records."""
    if not date_str:
        return None
    for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y", "%b %d, %Y", "%B %d, %Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def years_since(date_str):
    """Calculate years since a given date string."""
    dt = parse_date(date_str) if isinstance(date_str, str) else date_str
    if not dt:
        return None
    delta = datetime.now() - dt
    return round(delta.days / 365.25, 1)


# ─────────────────────────────────────────────────────────────
#  SELENIUM BROWSER SETUP
# ─────────────────────────────────────────────────────────────

def get_driver():
    """Create a headless Chrome WebDriver instance."""
    if not SELENIUM_AVAILABLE:
        return None
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(SELENIUM_TIMEOUT)
        return driver
    except Exception as e:
        print(f"    ⚠ Could not start Chrome: {e}")
        print(f"    💡 Install: pip install selenium && download chromedriver")
        return None


# ─────────────────────────────────────────────────────────────
#  ACCELA CITIZEN ACCESS SCRAPER (Osceola, Polk, Brevard, Lake)
# ─────────────────────────────────────────────────────────────

def scrape_accela(driver, portal_url, address):
    """
    Scrape an Accela Citizen Access portal for permits at an address.
    Used by: Osceola, Polk, Brevard, Lake counties.
    """
    permits = []

    try:
        driver.get(portal_url)
        time.sleep(3)

        # Parse address into street number and street name
        parts = address.split(",")[0].strip().split(" ", 1)
        if len(parts) < 2:
            return permits

        street_num = parts[0]
        street_name = parts[1].split(",")[0].strip()
        # Remove unit/apt info
        for prefix in ["Apt ", "Unit ", "Suite ", "#", "Ste "]:
            idx = street_name.find(prefix)
            if idx > 0:
                street_name = street_name[:idx].strip()

        # Find and fill the address search fields
        # Accela typically has: Street No, Street Name, Search button
        wait = WebDriverWait(driver, SELENIUM_TIMEOUT)

        # Try common Accela field IDs
        street_no_ids = [
            "ctl00_PlaceHolderMain_generalSearchForm_txtGSAddress_TextBox_HouseNumberStart",
            "txtGSAddress_TextBox_HouseNumberStart",
        ]
        street_name_ids = [
            "ctl00_PlaceHolderMain_generalSearchForm_txtGSAddress_TextBox_StreetName",
            "txtGSAddress_TextBox_StreetName",
        ]

        # Try to find and fill street number
        for field_id in street_no_ids:
            try:
                elem = driver.find_element(By.ID, field_id)
                elem.clear()
                elem.send_keys(street_num)
                break
            except Exception:
                continue

        # Try to find and fill street name
        for field_id in street_name_ids:
            try:
                elem = driver.find_element(By.ID, field_id)
                elem.clear()
                elem.send_keys(street_name)
                break
            except Exception:
                continue

        # Click search button
        search_btns = driver.find_elements(By.CSS_SELECTOR,
            "a[id*='btnNewSearch'], input[id*='btnSearch'], button[id*='btnSearch']")
        if search_btns:
            search_btns[0].click()
            time.sleep(5)

        # Parse results table
        rows = driver.find_elements(By.CSS_SELECTOR, "table[id*='GridView'] tr, .ACA_TabRow")
        for row in rows[1:]:  # Skip header
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                permit = {
                    "permit_number": cells[0].text.strip(),
                    "type": cells[1].text.strip() if len(cells) > 1 else "",
                    "description": cells[2].text.strip() if len(cells) > 2 else "",
                    "date": cells[3].text.strip() if len(cells) > 3 else "",
                    "status": cells[4].text.strip() if len(cells) > 4 else "",
                    "source": "accela",
                }
                permit["category"], permit["priority"] = categorize_permit(
                    f"{permit['type']} {permit['description']}")
                permits.append(permit)

    except Exception as e:
        print(f"    ⚠ Accela scrape error: {e}")

    return permits


# ─────────────────────────────────────────────────────────────
#  ORANGE COUNTY — FastTrack Portal
# ─────────────────────────────────────────────────────────────

def scrape_orange_permits(driver, address):
    """Scrape Orange County FastTrack portal for permits."""
    permits = []
    portal_url = COUNTIES["orange"]["permits_url"]

    try:
        driver.get(portal_url)
        time.sleep(3)

        # FastTrack has an address search — look for the input
        search_inputs = driver.find_elements(By.CSS_SELECTOR,
            "input[type='text'], input[placeholder*='address'], input[name*='address']")

        street_address = address.split(",")[0].strip()

        for inp in search_inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            name = inp.get_attribute("name") or ""
            if "address" in placeholder.lower() or "address" in name.lower() or "street" in name.lower():
                inp.clear()
                inp.send_keys(street_address)
                inp.send_keys(Keys.RETURN)
                time.sleep(5)
                break

        # Parse results
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr, .search-result-row")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                permit = {
                    "permit_number": cells[0].text.strip(),
                    "description": " ".join(c.text.strip() for c in cells[1:3]),
                    "date": cells[-1].text.strip() if cells else "",
                    "status": "",
                    "source": "orange_fasttrack",
                }
                permit["category"], permit["priority"] = categorize_permit(permit["description"])
                permits.append(permit)

    except Exception as e:
        print(f"    ⚠ Orange County scrape error: {e}")

    return permits


# ─────────────────────────────────────────────────────────────
#  SEMINOLE COUNTY — Click2Gov Portal
# ─────────────────────────────────────────────────────────────

def scrape_seminole_permits(driver, address):
    """Scrape Seminole County Click2Gov portal for permits."""
    permits = []
    portal_url = COUNTIES["seminole"]["permits_url"]

    try:
        driver.get(portal_url)
        time.sleep(3)

        street_address = address.split(",")[0].strip()

        # Click2Gov typically has address search
        search_inputs = driver.find_elements(By.CSS_SELECTOR,
            "input[type='text'], input[id*='address'], input[name*='address']")
        for inp in search_inputs:
            try:
                inp.clear()
                inp.send_keys(street_address)
                inp.send_keys(Keys.RETURN)
                time.sleep(5)
                break
            except Exception:
                continue

        # Parse results
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr, .result-row")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                permit = {
                    "permit_number": cells[0].text.strip(),
                    "description": " ".join(c.text.strip() for c in cells[1:3]),
                    "date": cells[-1].text.strip() if cells else "",
                    "status": "",
                    "source": "seminole_click2gov",
                }
                permit["category"], permit["priority"] = categorize_permit(permit["description"])
                permits.append(permit)

    except Exception as e:
        print(f"    ⚠ Seminole County scrape error: {e}")

    return permits


# ─────────────────────────────────────────────────────────────
#  VOLUSIA COUNTY — ConnectLive Portal
# ─────────────────────────────────────────────────────────────

def scrape_volusia_permits(driver, address):
    """Scrape Volusia County ConnectLive portal for permits."""
    permits = []
    portal_url = COUNTIES["volusia"]["permits_url"]

    try:
        driver.get(portal_url)
        time.sleep(3)

        street_address = address.split(",")[0].strip()

        search_inputs = driver.find_elements(By.CSS_SELECTOR,
            "input[type='text'], input[placeholder*='address']")
        for inp in search_inputs:
            try:
                inp.clear()
                inp.send_keys(street_address)
                inp.send_keys(Keys.RETURN)
                time.sleep(5)
                break
            except Exception:
                continue

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                permit = {
                    "permit_number": cells[0].text.strip(),
                    "description": " ".join(c.text.strip() for c in cells[1:3]),
                    "date": cells[-1].text.strip() if cells else "",
                    "status": "",
                    "source": "volusia_connectlive",
                }
                permit["category"], permit["priority"] = categorize_permit(permit["description"])
                permits.append(permit)

    except Exception as e:
        print(f"    ⚠ Volusia County scrape error: {e}")

    return permits


# ─────────────────────────────────────────────────────────────
#  SHOVELS.AI API (Paid — future upgrade path)
# ─────────────────────────────────────────────────────────────

def fetch_shovels_permits(address, api_key):
    """
    Fetch permit data from Shovels.ai API.
    This is the paid upgrade path — more reliable than scraping.
    """
    permits = []
    if not api_key:
        return permits

    try:
        base = "https://api.shovels.ai/v2/permits"
        params = urllib.parse.urlencode({"address": address})
        req = urllib.request.Request(
            f"{base}?{params}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "AGX-PropertyIntel/2.0",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for record in data.get("permits", data.get("results", [])):
            permit = {
                "permit_number": record.get("permit_number", ""),
                "type": record.get("type", ""),
                "description": record.get("description", ""),
                "date": record.get("issue_date", record.get("filed_date", "")),
                "status": record.get("status", ""),
                "source": "shovels_api",
            }
            permit["category"], permit["priority"] = categorize_permit(
                f"{permit['type']} {permit['description']}")
            permits.append(permit)

    except Exception as e:
        print(f"    ⚠ Shovels API error: {e}")

    return permits


# ─────────────────────────────────────────────────────────────
#  MAIN PERMIT SCANNER
# ─────────────────────────────────────────────────────────────

def get_county_scraper(county):
    """Get the appropriate scraper function for a county."""
    scrapers = {
        "orange": scrape_orange_permits,
        "seminole": scrape_seminole_permits,
        "osceola": lambda driver, addr: scrape_accela(driver, COUNTIES["osceola"]["permits_url"], addr),
        "polk": lambda driver, addr: scrape_accela(driver, COUNTIES["polk"]["permits_url"], addr),
        "brevard": lambda driver, addr: scrape_accela(driver, COUNTIES["brevard"]["permits_url"], addr),
        "volusia": scrape_volusia_permits,
        "lake": lambda driver, addr: scrape_accela(driver, COUNTIES["lake"]["permits_url"], addr),
    }
    return scrapers.get(county)


def extract_last_permits(permits):
    """
    From a list of permits, find the most recent of each key type.
    Returns dict with last_roof, last_paint, last_structural dates.
    """
    last_dates = {
        "last_roof_permit": None,
        "last_paint_permit": None,
        "last_structural_permit": None,
    }

    category_map = {
        "roofing": "last_roof_permit",
        "painting": "last_paint_permit",
        "structural": "last_structural_permit",
        "waterproofing": "last_roof_permit",  # related to roofing
    }

    for permit in permits:
        cat = permit.get("category", "other")
        date_key = category_map.get(cat)
        if date_key and permit.get("date"):
            dt = parse_date(permit["date"])
            if dt:
                current = parse_date(last_dates[date_key]) if last_dates[date_key] else None
                if not current or dt > current:
                    last_dates[date_key] = permit["date"]

    return last_dates


def scan_all_permits(db):
    """
    Scan all properties for permit history.
    Uses paid API if available, otherwise Selenium scraping.
    """
    print("\n" + "=" * 60)
    print("  MODULE 3: Permit History Scanner")
    print("=" * 60)

    properties = db.get_all()
    if not properties:
        print("  No properties in database to scan.")
        return 0

    # Decide which mode to use
    use_api = bool(SHOVELS_API_KEY)
    use_selenium = not use_api and SELENIUM_AVAILABLE

    if use_api:
        print("  📡 Using Shovels.ai API for permit data")
    elif use_selenium:
        print("  🌐 Using Selenium browser automation (free mode)")
    else:
        print("  ⚠️  No permit data source available!")
        print("     Option 1: pip install selenium (+ chromedriver) for free scraping")
        print("     Option 2: Set SHOVELS_API_KEY for paid API access")
        return 0

    driver = None
    if use_selenium:
        driver = get_driver()
        if not driver:
            print("  ⚠️  Could not start Selenium — skipping permits")
            return 0

    scanned = 0
    found = 0

    try:
        for prop in properties:
            address = prop.get("address", "")
            county = prop.get("county", "unknown")
            print(f"  🔎 {prop['name']} ({county})...")

            permits = []

            if use_api:
                permits = fetch_shovels_permits(address, SHOVELS_API_KEY)
            elif use_selenium and county != "unknown":
                scraper = get_county_scraper(county)
                if scraper:
                    permits = scraper(driver, address)
                else:
                    print(f"    ⚠ No scraper for {county} county")

            if permits:
                last_dates = extract_last_permits(permits)
                db.upsert(address, {
                    "permits": permits,
                    **last_dates,
                    "permit_scan_date": datetime.now().isoformat(),
                })
                found += 1
                print(f"    ✓ {len(permits)} permits found")

                # Flag overdue items
                for key, label, threshold in [
                    ("last_roof_permit", "Roof", ROOF_AGE_ALERT_YEARS),
                    ("last_paint_permit", "Paint", PAINT_AGE_ALERT_YEARS),
                ]:
                    if last_dates.get(key):
                        yrs = years_since(last_dates[key])
                        if yrs and yrs > threshold:
                            print(f"    🔴 {label}: {yrs} years ago (>{threshold}yr threshold)")
            else:
                db.upsert(address, {"permit_scan_date": datetime.now().isoformat()})
                print(f"    — No permits found")

            scanned += 1
            time.sleep(1)

    finally:
        if driver:
            driver.quit()

    print(f"\n  ✅ Scanned {scanned} properties, {found} with permit records")
    return found
