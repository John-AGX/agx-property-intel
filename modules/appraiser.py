"""
AGX Property Intelligence — Property Appraiser Scraper Module

Scrapes county property appraiser websites to find:
- Owner name & management company
- Year built
- Number of units / buildings
- Total square footage
- Assessed value
- Parcel ID
- Land use classification

Requires Selenium for browser automation (all 7 counties use JS-heavy portals).
"""

import re
import time
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import COUNTIES, SELENIUM_TIMEOUT

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


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
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(SELENIUM_TIMEOUT)
        return driver
    except Exception as e:
        print(f"    ⚠ Could not start Chrome: {e}")
        return None


def extract_number(text):
    """Extract first number from text."""
    if not text:
        return None
    match = re.search(r'[\d,]+', str(text).replace(",", ""))
    return int(match.group().replace(",", "")) if match else None


def extract_year(text):
    """Extract a 4-digit year from text."""
    if not text:
        return None
    match = re.search(r'(19|20)\d{2}', str(text))
    return int(match.group()) if match else None


def extract_currency(text):
    """Extract dollar amount from text."""
    if not text:
        return None
    match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', str(text).replace(",", ""))
    return float(match.group(1).replace(",", "")) if match else None


# ─────────────────────────────────────────────────────────────
#  GENERIC APPRAISER SCRAPER
# ─────────────────────────────────────────────────────────────

def scrape_appraiser_generic(driver, search_url, address):
    """
    Generic appraiser scraper that works for most county portals.
    Searches by address and extracts property details from the results page.
    """
    info = {}

    try:
        driver.get(search_url)
        time.sleep(3)

        # Parse the street address (before the city)
        street_address = address.split(",")[0].strip()

        # Look for search input fields
        search_inputs = driver.find_elements(By.CSS_SELECTOR, " ".join([
            "input[type='text']",
        ]))

        # Also try specific patterns
        for selector in [
            "input[id*='address']", "input[name*='address']",
            "input[id*='street']", "input[name*='street']",
            "input[placeholder*='address']", "input[placeholder*='Address']",
            "input[id*='search']", "input[name*='search']",
        ]:
            found = driver.find_elements(By.CSS_SELECTOR, selector)
            if found:
                search_inputs = found
                break

        if search_inputs:
            search_inputs[0].clear()
            search_inputs[0].send_keys(street_address)
            search_inputs[0].send_keys(Keys.RETURN)
            time.sleep(5)

        # Try clicking first result link if there's a results table
        result_links = driver.find_elements(By.CSS_SELECTOR,
            "table tbody tr td a, .search-result a, .result-item a")
        if result_links:
            result_links[0].click()
            time.sleep(3)

        # Now extract property details from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Look for common labels and extract values
        label_patterns = {
            "owner_name": [
                r"(?:Owner|Property Owner|Owner Name)[:\s]*([^\n]+)",
                r"(?:Name)[:\s]*([^\n]+?)(?:Address|Mail|Phone)",
            ],
            "mailing_address": [
                r"(?:Mailing Address|Mail Address|Owner Address)[:\s]*([^\n]+)",
            ],
            "year_built": [
                r"(?:Year Built|Yr Built|Built)[:\s]*(\d{4})",
                r"(?:Effective Year|Actual Year)[:\s]*(\d{4})",
            ],
            "total_sqft": [
                r"(?:Total (?:Sq\.?|Square)\s*(?:Ft\.?|Feet|Footage))[:\s]*([\d,]+)",
                r"(?:Building Area|Living Area|Heated Area|Adj Area)[:\s]*([\d,]+)",
            ],
            "assessed_value": [
                r"(?:Just Value|Total Value|Assessed Value|Market Value)[:\s]*\$?([\d,]+)",
            ],
            "land_use": [
                r"(?:Land Use|Use Code|Property Use|Zoning)[:\s]*([^\n]+)",
            ],
            "parcel_id": [
                r"(?:Parcel|Parcel ID|Parcel Number|Account|Folio)[:\s#]*([\d\-\.]+)",
            ],
        }

        for field, patterns in label_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if field == "year_built":
                        info[field] = extract_year(value)
                    elif field == "total_sqft":
                        info[field] = extract_number(value)
                    elif field == "assessed_value":
                        info[field] = extract_currency(value)
                    else:
                        info[field] = value
                    break

        # Try to find unit count (apartments)
        unit_patterns = [
            r"(\d+)\s*(?:units?|apartments?|dwelling)",
            r"(?:Units?|No\.? of Units)[:\s]*(\d+)",
            r"(?:Living Units)[:\s]*(\d+)",
        ]
        for pattern in unit_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                info["units"] = int(match.group(1))
                break

        # Try to find building count
        building_patterns = [
            r"(\d+)\s*(?:buildings?|structures?)",
            r"(?:Buildings?|No\.? of Buildings)[:\s]*(\d+)",
        ]
        for pattern in building_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                info["buildings"] = int(match.group(1))
                break

    except Exception as e:
        print(f"    ⚠ Appraiser scrape error: {e}")

    return info


# ─────────────────────────────────────────────────────────────
#  COUNTY-SPECIFIC OVERRIDES
# ─────────────────────────────────────────────────────────────

def scrape_orange_appraiser(driver, address):
    """Orange County Property Appraiser — ocpafl.org"""
    return scrape_appraiser_generic(driver, COUNTIES["orange"]["appraiser_search"], address)


def scrape_seminole_appraiser(driver, address):
    """Seminole County Property Appraiser — scpafl.org"""
    return scrape_appraiser_generic(driver, COUNTIES["seminole"]["appraiser_search"], address)


def scrape_osceola_appraiser(driver, address):
    """Osceola County Property Appraiser"""
    return scrape_appraiser_generic(driver, COUNTIES["osceola"]["appraiser_search"], address)


def scrape_polk_appraiser(driver, address):
    """Polk County Property Appraiser"""
    return scrape_appraiser_generic(driver, COUNTIES["polk"]["appraiser_search"], address)


def scrape_brevard_appraiser(driver, address):
    """Brevard County Property Appraiser"""
    return scrape_appraiser_generic(driver, COUNTIES["brevard"]["appraiser_search"], address)


def scrape_volusia_appraiser(driver, address):
    """Volusia County Property Appraiser"""
    return scrape_appraiser_generic(driver, COUNTIES["volusia"]["appraiser_search"], address)


def scrape_lake_appraiser(driver, address):
    """Lake County Property Appraiser"""
    return scrape_appraiser_generic(driver, COUNTIES["lake"]["appraiser_search"], address)


APPRAISER_SCRAPERS = {
    "orange": scrape_orange_appraiser,
    "seminole": scrape_seminole_appraiser,
    "osceola": scrape_osceola_appraiser,
    "polk": scrape_polk_appraiser,
    "brevard": scrape_brevard_appraiser,
    "volusia": scrape_volusia_appraiser,
    "lake": scrape_lake_appraiser,
}


# ─────────────────────────────────────────────────────────────
#  MAIN APPRAISER SCANNER
# ─────────────────────────────────────────────────────────────

def scan_all_appraisers(db):
    """
    Scan all properties for owner/building info from county appraiser sites.
    """
    print("\n" + "=" * 60)
    print("  MODULE 4: Property Appraiser Scanner")
    print("=" * 60)

    if not SELENIUM_AVAILABLE:
        print("  ⚠️  Selenium not installed — skipping appraiser lookups")
        print("     Install: pip install selenium")
        return 0

    properties = db.get_all()
    if not properties:
        print("  No properties to scan.")
        return 0

    driver = get_driver()
    if not driver:
        return 0

    scanned = 0
    found = 0

    try:
        for prop in properties:
            address = prop.get("address", "")
            county = prop.get("county", "unknown")

            # Skip if already scanned recently (within 30 days)
            if prop.get("appraiser_scan_date"):
                from datetime import timedelta
                last_scan = datetime.fromisoformat(prop["appraiser_scan_date"])
                if datetime.now() - last_scan < timedelta(days=30):
                    continue

            print(f"  🔎 {prop['name']} ({county})...")

            scraper = APPRAISER_SCRAPERS.get(county)
            if not scraper:
                print(f"    ⚠ No appraiser scraper for {county}")
                continue

            info = scraper(driver, address)

            if info:
                db.upsert(address, {
                    "owner_info": info,
                    "appraiser_scan_date": datetime.now().isoformat(),
                })
                found += 1
                owner = info.get("owner_name", "Unknown")
                year = info.get("year_built", "?")
                print(f"    ✓ Owner: {owner} | Built: {year}")
            else:
                db.upsert(address, {"appraiser_scan_date": datetime.now().isoformat()})
                print(f"    — No data found")

            scanned += 1
            time.sleep(2)  # Be polite to county servers

    finally:
        driver.quit()

    print(f"\n  ✅ Scanned {scanned} properties, {found} with appraiser data")
    return found
