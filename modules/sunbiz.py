"""
AGX Property Intelligence — Florida Sunbiz Corporate Entity Lookup

Searches Florida Division of Corporations (sunbiz.org) to find:
- Management company / LLC details
- Registered agent (often the decision maker)
- Officers and directors
- Entity status (active/inactive)
- Filing date

Uses Selenium to navigate the JavaScript-heavy search portal.
"""

import re
import time
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SELENIUM_TIMEOUT

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

SUNBIZ_SEARCH_URL = "https://search.sunbiz.org/Inquiry/CorporationSearch/ByName"


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


def clean_entity_name(owner_name):
    """
    Clean an owner name from property records into something searchable on Sunbiz.
    E.g., "ARDEN VILLAS LLC" → "ARDEN VILLAS"
    """
    if not owner_name:
        return ""

    name = owner_name.upper().strip()

    # Remove common suffixes that might cause search issues
    for suffix in [" LLC", " L.L.C.", " LP", " L.P.", " INC", " INC.", " CORP", " CORP.",
                   " CO", " CO.", " LTD", " LTD.", " TRUST", " TRUSTEE",
                   " ET AL", " ETAL", " %", " C/O"]:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()

    # Remove trailing punctuation
    name = name.rstrip(",.-")

    return name


def search_sunbiz(driver, entity_name):
    """
    Search Florida Sunbiz for a corporate entity.
    Returns dict with entity details or empty dict.
    """
    info = {}

    try:
        driver.get(SUNBIZ_SEARCH_URL)
        time.sleep(2)

        # Find search input and enter entity name
        search_input = driver.find_element(By.CSS_SELECTOR,
            "input[id*='SearchName'], input[name*='SearchName'], input[type='text']")
        search_input.clear()
        search_input.send_keys(entity_name)

        # Click search button
        search_btns = driver.find_elements(By.CSS_SELECTOR,
            "input[type='submit'], button[type='submit']")
        if search_btns:
            search_btns[0].click()
            time.sleep(3)

        # Look for results — click first matching result
        result_links = driver.find_elements(By.CSS_SELECTOR,
            "a[href*='CorporationSearch/SearchResultDetail']")
        if result_links:
            # Find best match (closest to our search term)
            best_match = None
            for link in result_links:
                link_text = link.text.upper().strip()
                if entity_name.upper() in link_text or link_text in entity_name.upper():
                    best_match = link
                    break
            if not best_match:
                best_match = result_links[0]  # Take first result

            best_match.click()
            time.sleep(3)

            # Extract entity details from detail page
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # Entity name
            name_match = re.search(r"(?:Entity Name|Corporation Name)[:\s]*([^\n]+)", page_text, re.IGNORECASE)
            if name_match:
                info["entity_name"] = name_match.group(1).strip()

            # Entity type (LLC, Corp, LP, etc.)
            type_match = re.search(r"(?:Entity Type|Filing Type)[:\s]*([^\n]+)", page_text, re.IGNORECASE)
            if type_match:
                info["entity_type"] = type_match.group(1).strip()

            # Status
            status_match = re.search(r"(?:Status)[:\s]*(Active|Inactive|Dissolved|Revoked|Withdrawn)[^\n]*",
                                      page_text, re.IGNORECASE)
            if status_match:
                info["status"] = status_match.group(1).strip()

            # Filing date
            date_match = re.search(r"(?:Filing Date|Date Filed)[:\s]*(\d{1,2}/\d{1,2}/\d{4})", page_text)
            if date_match:
                info["filing_date"] = date_match.group(1)

            # Registered Agent
            agent_match = re.search(
                r"(?:Registered Agent)[:\s]*\n?([^\n]+)(?:\n([^\n]+))?",
                page_text, re.IGNORECASE
            )
            if agent_match:
                info["registered_agent"] = agent_match.group(1).strip()
                if agent_match.group(2):
                    info["agent_address"] = agent_match.group(2).strip()

            # Officers / Directors
            officers = []
            officer_section = re.findall(
                r"(?:Title|Name|Address)\s+([^\n]+)",
                page_text[page_text.lower().find("officer") if "officer" in page_text.lower() else 0:]
            )
            # Parse officer blocks
            current_officer = {}
            for line in officer_section[:20]:  # Limit to prevent runaway
                line = line.strip()
                if re.match(r"^(President|VP|Secretary|Treasurer|Director|Manager|Member|CEO|CFO|COO)",
                           line, re.IGNORECASE):
                    if current_officer:
                        officers.append(current_officer)
                    current_officer = {"title": line}
                elif current_officer and "name" not in current_officer:
                    current_officer["name"] = line
            if current_officer:
                officers.append(current_officer)

            info["officers"] = officers[:10]  # Cap at 10

    except Exception as e:
        print(f"    ⚠ Sunbiz lookup error: {e}")

    return info


def scan_all_entities(db):
    """
    Look up corporate entity info for all properties with owner data.
    """
    print("\n" + "=" * 60)
    print("  MODULE 5: Florida Sunbiz Corporate Lookup")
    print("=" * 60)

    if not SELENIUM_AVAILABLE:
        print("  ⚠️  Selenium not installed — skipping Sunbiz lookups")
        return 0

    properties = db.get_all()
    if not properties:
        print("  No properties to look up.")
        return 0

    # Only look up properties that have an owner name
    candidates = [p for p in properties
                  if p.get("owner_info", {}).get("owner_name")
                  and not p.get("sunbiz_scan_date")]

    if not candidates:
        print("  No properties with owner info to look up (or all already scanned).")
        return 0

    print(f"  Looking up {len(candidates)} entities on Sunbiz...")

    driver = get_driver()
    if not driver:
        return 0

    found = 0
    already_searched = set()  # Avoid duplicate searches for same owner

    try:
        for prop in candidates:
            owner = prop["owner_info"]["owner_name"]
            search_name = clean_entity_name(owner)

            if not search_name or search_name in already_searched:
                continue

            already_searched.add(search_name)
            print(f"  🔎 {search_name}...")

            info = search_sunbiz(driver, search_name)

            if info:
                db.upsert(prop["address"], {
                    "corporate_info": info,
                    "sunbiz_scan_date": datetime.now().isoformat(),
                })
                found += 1
                status = info.get("status", "?")
                agent = info.get("registered_agent", "?")
                print(f"    ✓ {info.get('entity_name', search_name)} — {status}")
                print(f"      Agent: {agent}")
            else:
                db.upsert(prop["address"], {"sunbiz_scan_date": datetime.now().isoformat()})
                print(f"    — Not found on Sunbiz")

            time.sleep(2)

    finally:
        driver.quit()

    print(f"\n  ✅ Looked up {len(already_searched)} entities, {found} found on Sunbiz")
    return found
