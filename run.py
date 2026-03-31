#!/usr/bin/env python3
"""
AGX Central Florida — Property Intelligence System
===================================================

Full-stack lead generation tool that builds comprehensive property profiles
for multifamily apartment complexes across Central Florida.

Usage:
    python run.py --demo                    # Demo dashboard with sample data
    python run.py --full --key YOUR_KEY     # Full scan (all modules)
    python run.py --discover --key KEY      # Discovery + reviews only
    python run.py --permits                 # Permit scan only (Selenium)
    python run.py --appraiser               # Property appraiser scan only
    python run.py --sunbiz                  # Sunbiz lookup only
    python run.py --score                   # Re-score all properties
    python run.py --dashboard               # Regenerate dashboard only

Requirements:
    - Python 3.8+
    - Google Places API key (for discovery + reviews)
    - Selenium + ChromeDriver (for permits, appraiser, sunbiz — free mode)
    - OR Shovels.ai API key (for permits — paid mode)
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import GOOGLE_PLACES_API_KEY, DB_FILE, OUTPUT_FILE
from modules.database import PropertyDatabase


def run_demo(db):
    """Load realistic demo data into the database."""
    print("\n  📋 Loading demo data for Central FL apartment complexes...\n")

    demo_properties = [
        {
            "name": "Azalea Park Apartments",
            "address": "4820 S Semoran Blvd, Orlando, FL 32822",
            "county": "orange",
            "phone": "(407) 555-0142",
            "website": "",
            "google_url": "https://maps.google.com/?cid=example1",
            "google_rating": 2.1,
            "total_reviews": 287,
            "owner_info": {
                "owner_name": "AZALEA PARK HOLDINGS LLC",
                "mailing_address": "1200 Brickell Ave, Miami, FL 33131",
                "year_built": 1988,
                "units": 248,
                "buildings": 12,
                "total_sqft": 218000,
                "assessed_value": 14500000,
                "land_use": "Multi-Family Residential",
                "parcel_id": "25-2245-0000-00-001",
            },
            "permits": [
                {"permit_number": "BLD-2011-04522", "type": "Roof", "description": "Re-roof buildings 1-4 shingle", "date": "03/15/2011", "status": "Finaled", "category": "roofing", "priority": "high", "source": "orange_fasttrack"},
                {"permit_number": "BLD-2016-11234", "type": "Paint", "description": "Exterior painting all buildings", "date": "08/22/2016", "status": "Finaled", "category": "painting", "priority": "high", "source": "orange_fasttrack"},
                {"permit_number": "BLD-2019-08811", "type": "Structural", "description": "Balcony repair building 7", "date": "11/03/2019", "status": "Finaled", "category": "structural", "priority": "high", "source": "orange_fasttrack"},
            ],
            "last_roof_permit": "03/15/2011",
            "last_paint_permit": "08/22/2016",
            "last_structural_permit": "11/03/2019",
            "corporate_info": {
                "entity_name": "AZALEA PARK HOLDINGS LLC",
                "entity_type": "Florida Limited Liability Company",
                "status": "Active",
                "registered_agent": "Robert Chen",
                "agent_address": "1200 Brickell Ave Suite 400, Miami, FL 33131",
                "filing_date": "04/12/2005",
                "officers": [{"title": "Manager", "name": "Robert Chen"}, {"title": "Manager", "name": "Pacific Coast Capital Group"}],
            },
            "review_issues": [
                {"category": "Roofing & Water Intrusion", "icon": "🏚️", "severity": 9.0, "rating": 1, "author": "Maria G.", "time": "2 months ago", "excerpt": "Every time it rains the ceiling leaks in our bedroom and the living room. They put a bucket and said they'd fix it — that was 6 months ago", "keyword_count": 3},
                {"category": "Roofing & Water Intrusion", "icon": "🏚️", "severity": 7.5, "rating": 1, "author": "DeShawn W.", "time": "1 month ago", "excerpt": "Water damage all over the ceiling in building 4. You can see the water stains from outside", "keyword_count": 2},
                {"category": "Mold & Moisture", "icon": "🦠", "severity": 7.2, "rating": 1, "author": "Jessica T.", "time": "3 weeks ago", "excerpt": "Black mold growing on the walls near where the roof leaks. My kids have been getting sick", "keyword_count": 3},
                {"category": "General Exterior Neglect", "icon": "⚠️", "severity": 5.5, "rating": 1, "author": "Tanya R.", "time": "1 month ago", "excerpt": "This place is falling apart and they refuse to fix anything. Multiple code violations", "keyword_count": 4},
            ],
        },
        {
            "name": "Cypress Pointe at Kissimmee",
            "address": "8651 Treasure Island Rd, Kissimmee, FL 34747",
            "county": "osceola",
            "phone": "(407) 555-0198",
            "google_url": "https://maps.google.com/?cid=example2",
            "google_rating": 2.4,
            "total_reviews": 412,
            "owner_info": {
                "owner_name": "CYPRESS POINTE RESORT VENTURES LLC",
                "year_built": 1996,
                "units": 336,
                "buildings": 18,
                "total_sqft": 312000,
                "assessed_value": 22800000,
                "land_use": "Multi-Family Residential",
                "parcel_id": "01-25-27-4892-0001-00A0",
            },
            "permits": [
                {"permit_number": "BP-2009-3321", "type": "Roof", "description": "Complete re-roof buildings 1-8", "date": "07/10/2009", "status": "Finaled", "category": "roofing", "priority": "high", "source": "accela"},
                {"permit_number": "BP-2014-7782", "type": "Stucco", "description": "Stucco repair and paint bldgs 9-18", "date": "04/18/2014", "status": "Finaled", "category": "stucco_siding", "priority": "medium", "source": "accela"},
            ],
            "last_roof_permit": "07/10/2009",
            "last_paint_permit": "04/18/2014",
            "corporate_info": {
                "entity_name": "CYPRESS POINTE RESORT VENTURES LLC",
                "entity_type": "Florida Limited Liability Company",
                "status": "Active",
                "registered_agent": "CT Corporation System",
                "filing_date": "02/28/2003",
                "officers": [{"title": "Manager", "name": "Starwood Property Trust"}],
            },
            "review_issues": [
                {"category": "Foundation & Structural", "icon": "🏗️", "severity": 8.5, "rating": 1, "author": "Robert H.", "time": "3 months ago", "excerpt": "Cracks running down the walls in multiple units. Foundation issues that management pretends don't exist", "keyword_count": 3},
                {"category": "Siding & Stucco", "icon": "🧱", "severity": 5.0, "rating": 2, "author": "Michael P.", "time": "2 months ago", "excerpt": "Stucco crumbling off the exterior walls on all the buildings. Paint peeling everywhere", "keyword_count": 3},
                {"category": "Roofing & Water Intrusion", "icon": "🏚️", "severity": 7.5, "rating": 1, "author": "Lisa K.", "time": "6 weeks ago", "excerpt": "Roof leak in building 12. Water comes pouring in when it rains. They just put tarps on the roof", "keyword_count": 3},
            ],
        },
        {
            "name": "Lakeshore Reserve",
            "address": "3200 Lakeshore Blvd, Lakeland, FL 33803",
            "county": "polk",
            "phone": "(863) 555-0156",
            "google_url": "https://maps.google.com/?cid=example3",
            "google_rating": 2.7,
            "total_reviews": 198,
            "owner_info": {
                "owner_name": "LAKESHORE MULTIFAMILY PARTNERS LP",
                "year_built": 1992,
                "units": 192,
                "buildings": 10,
                "total_sqft": 164000,
                "assessed_value": 11200000,
                "land_use": "Multi-Family Residential",
            },
            "permits": [
                {"permit_number": "PK-2013-5567", "type": "Roof", "description": "Partial re-roof bldgs 3,5", "date": "09/22/2013", "status": "Finaled", "category": "roofing", "priority": "high", "source": "accela"},
                {"permit_number": "PK-2018-2290", "type": "Paving", "description": "Parking lot resurfacing", "date": "05/11/2018", "status": "Finaled", "category": "paving", "priority": "medium", "source": "accela"},
            ],
            "last_roof_permit": "09/22/2013",
            "corporate_info": {
                "entity_name": "LAKESHORE MULTIFAMILY PARTNERS LP",
                "status": "Active",
                "registered_agent": "James McAllister",
                "officers": [{"title": "General Partner", "name": "James McAllister"}, {"title": "Limited Partner", "name": "Southeast Capital LLC"}],
            },
            "review_issues": [
                {"category": "Roofing & Water Intrusion", "icon": "🏚️", "severity": 9.0, "rating": 1, "author": "Jennifer S.", "time": "2 weeks ago", "excerpt": "Roof is completely shot on buildings 3 and 5. They've had tarps up for 8 months with no repair", "keyword_count": 3},
                {"category": "Parking & Paving", "icon": "🅿️", "severity": 4.8, "rating": 2, "author": "Brandon T.", "time": "1 month ago", "excerpt": "Parking lot is destroyed — potholes everywhere. Asphalt hasn't been resurfaced in years", "keyword_count": 4},
                {"category": "Mold & Moisture", "icon": "🦠", "severity": 6.0, "rating": 1, "author": "Sarah L.", "time": "3 weeks ago", "excerpt": "Mold growing on the outside of the buildings and inside our unit from all the moisture", "keyword_count": 3},
            ],
        },
        {
            "name": "Palm Bay Crossings",
            "address": "1890 Palm Bay Rd NE, Palm Bay, FL 32905",
            "county": "brevard",
            "phone": "(321) 555-0177",
            "google_url": "https://maps.google.com/?cid=example4",
            "google_rating": 2.3,
            "total_reviews": 156,
            "owner_info": {
                "owner_name": "PALM BAY RESIDENTIAL GROUP INC",
                "year_built": 1985,
                "units": 164,
                "buildings": 8,
                "total_sqft": 142000,
                "assessed_value": 8900000,
                "land_use": "Multi-Family Residential",
            },
            "permits": [
                {"permit_number": "BR-2008-12445", "type": "Roof", "description": "Re-roof all buildings", "date": "11/08/2008", "status": "Finaled", "category": "roofing", "priority": "high", "source": "accela"},
                {"permit_number": "BR-2015-06721", "type": "Paint", "description": "Exterior paint buildings 1-8", "date": "03/27/2015", "status": "Finaled", "category": "painting", "priority": "high", "source": "accela"},
            ],
            "last_roof_permit": "11/08/2008",
            "last_paint_permit": "03/27/2015",
            "corporate_info": {
                "entity_name": "PALM BAY RESIDENTIAL GROUP INC",
                "status": "Active",
                "registered_agent": "Patricia Donovan",
            },
            "review_issues": [
                {"category": "Siding & Stucco", "icon": "🧱", "severity": 6.0, "rating": 1, "author": "Nicole B.", "time": "1 month ago", "excerpt": "Siding falling off the buildings. Wood rot everywhere on the balconies", "keyword_count": 3},
                {"category": "Foundation & Structural", "icon": "🏗️", "severity": 7.8, "rating": 1, "author": "James C.", "time": "3 weeks ago", "excerpt": "Huge cracks in the foundation and up the walls. Building is unsafe", "keyword_count": 4},
                {"category": "General Exterior Neglect", "icon": "⚠️", "severity": 5.5, "rating": 1, "author": "Patricia D.", "time": "2 months ago", "excerpt": "Management won't fix anything. Failed inspection and still no repairs", "keyword_count": 3},
            ],
        },
        {
            "name": "Seminole Crossings",
            "address": "500 Wymore Rd, Altamonte Springs, FL 32714",
            "county": "seminole",
            "phone": "(407) 555-0189",
            "google_url": "https://maps.google.com/?cid=example5",
            "google_rating": 2.6,
            "total_reviews": 321,
            "owner_info": {
                "owner_name": "SEMINOLE CROSSINGS APARTMENTS LLC",
                "year_built": 1991,
                "units": 280,
                "buildings": 14,
                "total_sqft": 245000,
                "assessed_value": 18600000,
                "land_use": "Multi-Family Residential",
            },
            "permits": [
                {"permit_number": "SC-2010-08832", "type": "Roof", "description": "Complete re-roof all buildings", "date": "06/14/2010", "status": "Finaled", "category": "roofing", "priority": "high", "source": "click2gov"},
                {"permit_number": "SC-2017-03345", "type": "Paint", "description": "Full exterior repaint", "date": "02/09/2017", "status": "Finaled", "category": "painting", "priority": "high", "source": "click2gov"},
                {"permit_number": "SC-2022-11990", "type": "Structural", "description": "Stairwell structural repair bldg 9", "date": "08/30/2022", "status": "Finaled", "category": "structural", "priority": "high", "source": "click2gov"},
            ],
            "last_roof_permit": "06/14/2010",
            "last_paint_permit": "02/09/2017",
            "last_structural_permit": "08/30/2022",
            "corporate_info": {
                "entity_name": "SEMINOLE CROSSINGS APARTMENTS LLC",
                "status": "Active",
                "registered_agent": "National Registered Agents Inc",
                "officers": [{"title": "Manager", "name": "Greystone Property Management"}, {"title": "Member", "name": "Southeast Multi Holdings LLC"}],
            },
            "review_issues": [
                {"category": "Roofing & Water Intrusion", "icon": "🏚️", "severity": 9.0, "rating": 1, "author": "Angela W.", "time": "2 weeks ago", "excerpt": "Roof leak has been going on since Hurricane Ian. That's over THREE YEARS and still not fixed", "keyword_count": 3},
                {"category": "Mold & Moisture", "icon": "🦠", "severity": 7.2, "rating": 1, "author": "Marcus H.", "time": "1 month ago", "excerpt": "Mold from the roof leaks has spread to three rooms. Black mold on the walls", "keyword_count": 3},
                {"category": "Foundation & Structural", "icon": "🏗️", "severity": 5.2, "rating": 2, "author": "Laura K.", "time": "6 weeks ago", "excerpt": "Cracks running through walls in building 9. Foundation is settling", "keyword_count": 3},
            ],
        },
        {
            "name": "Sandpiper Village",
            "address": "2450 W International Speedway Blvd, Daytona Beach, FL 32114",
            "county": "volusia",
            "phone": "(386) 555-0134",
            "google_url": "https://maps.google.com/?cid=example6",
            "google_rating": 2.9,
            "total_reviews": 234,
            "owner_info": {
                "owner_name": "SANDPIPER VILLAGE INVESTORS LLC",
                "year_built": 1994,
                "units": 210,
                "buildings": 11,
                "total_sqft": 185000,
                "assessed_value": 13100000,
                "land_use": "Multi-Family Residential",
            },
            "permits": [
                {"permit_number": "VL-2012-07744", "type": "Roof", "description": "Re-roof buildings 1-6", "date": "04/05/2012", "status": "Finaled", "category": "roofing", "priority": "high", "source": "connectlive"},
                {"permit_number": "VL-2020-01123", "type": "Paint", "description": "Exterior paint phase 1", "date": "01/20/2020", "status": "Finaled", "category": "painting", "priority": "high", "source": "connectlive"},
            ],
            "last_roof_permit": "04/05/2012",
            "last_paint_permit": "01/20/2020",
            "review_issues": [
                {"category": "Roofing & Water Intrusion", "icon": "🏚️", "severity": 7.5, "rating": 1, "author": "Crystal A.", "time": "1 month ago", "excerpt": "Building 8 roof has been leaking for over a year. Water damage visible from outside", "keyword_count": 3},
                {"category": "Parking & Paving", "icon": "🅿️", "severity": 3.2, "rating": 2, "author": "Stephanie V.", "time": "2 months ago", "excerpt": "Parking lot is a disaster. Potholes big enough to lose a tire in", "keyword_count": 3},
            ],
        },
        {
            "name": "The Groves at Clermont",
            "address": "1100 Hooks St, Clermont, FL 34711",
            "county": "lake",
            "phone": "(352) 555-0145",
            "google_url": "https://maps.google.com/?cid=example7",
            "google_rating": 3.2,
            "total_reviews": 145,
            "owner_info": {
                "owner_name": "CLERMONT GROVES APARTMENTS LP",
                "year_built": 2001,
                "units": 120,
                "buildings": 6,
                "total_sqft": 108000,
                "assessed_value": 9400000,
                "land_use": "Multi-Family Residential",
            },
            "permits": [
                {"permit_number": "LK-2015-04410", "type": "Roof", "description": "Roof repair buildings 2,4", "date": "10/12/2015", "status": "Finaled", "category": "roofing", "priority": "high", "source": "accela"},
                {"permit_number": "LK-2021-08876", "type": "Paint", "description": "Exterior repaint all buildings", "date": "06/30/2021", "status": "Finaled", "category": "painting", "priority": "high", "source": "accela"},
            ],
            "last_roof_permit": "10/12/2015",
            "last_paint_permit": "06/30/2021",
            "review_issues": [
                {"category": "Roofing & Water Intrusion", "icon": "🏚️", "severity": 6.0, "rating": 2, "author": "Michelle R.", "time": "1 month ago", "excerpt": "Roof leak in our unit getting worse every storm. Water stains all over", "keyword_count": 2},
                {"category": "Siding & Stucco", "icon": "🧱", "severity": 4.0, "rating": 2, "author": "Danny L.", "time": "5 weeks ago", "excerpt": "Exterior stucco cracking and peeling. Wood rot on the stairway railings", "keyword_count": 3},
            ],
        },
        {
            "name": "Harbour Isle at Deltona",
            "address": "850 Deltona Blvd, Deltona, FL 32725",
            "county": "volusia",
            "phone": "(386) 555-0167",
            "google_url": "https://maps.google.com/?cid=example8",
            "google_rating": 2.5,
            "total_reviews": 189,
            "owner_info": {
                "owner_name": "HARBOUR ISLE PROPERTY MANAGEMENT INC",
                "year_built": 1987,
                "units": 176,
                "buildings": 9,
                "total_sqft": 152000,
                "assessed_value": 10100000,
                "land_use": "Multi-Family Residential",
            },
            "permits": [
                {"permit_number": "VL-2007-09112", "type": "Roof", "description": "Re-roof all buildings", "date": "02/18/2007", "status": "Finaled", "category": "roofing", "priority": "high", "source": "connectlive"},
            ],
            "last_roof_permit": "02/18/2007",
            "corporate_info": {
                "entity_name": "HARBOUR ISLE PROPERTY MANAGEMENT INC",
                "status": "Active",
                "registered_agent": "William Harbour",
                "officers": [{"title": "President", "name": "William Harbour"}, {"title": "VP", "name": "Sandra Harbour"}],
            },
            "review_issues": [
                {"category": "Roofing & Water Intrusion", "icon": "🏚️", "severity": 7.5, "rating": 1, "author": "Brenda F.", "time": "3 weeks ago", "excerpt": "ROOF IS LEAKING IN 6 UNITS. Water damage everywhere. Tarps and nothing else", "keyword_count": 3},
                {"category": "General Exterior Neglect", "icon": "⚠️", "severity": 6.6, "rating": 1, "author": "Travis W.", "time": "1 month ago", "excerpt": "Falling apart, management refuses to fix anything. Multiple code violations", "keyword_count": 5},
            ],
        },
    ]

    for prop_data in demo_properties:
        address = prop_data["address"]
        template = db.new_property_template(prop_data["name"], address, prop_data.get("county", ""))
        template.update(prop_data)
        template["review_scan_date"] = datetime.now().isoformat()
        template["permit_scan_date"] = datetime.now().isoformat()
        template["appraiser_scan_date"] = datetime.now().isoformat()
        template["sunbiz_scan_date"] = datetime.now().isoformat()
        db.upsert(address, template)
        print(f"  ✓ {prop_data['name']} ({prop_data.get('county', '?')})")

    print(f"\n  Loaded {len(demo_properties)} demo properties.")


def main():
    args = sys.argv[1:]
    demo = "--demo" in args
    full = "--full" in args
    do_discover = "--discover" in args or full
    do_permits = "--permits" in args or full
    do_appraiser = "--appraiser" in args or full
    do_sunbiz = "--sunbiz" in args or full
    do_score = "--score" in args or full
    do_dashboard = "--dashboard" in args or full or demo

    # Get API key
    api_key = GOOGLE_PLACES_API_KEY
    for i, arg in enumerate(args):
        if arg == "--key" and i + 1 < len(args):
            api_key = args[i + 1]

    # Database
    db = PropertyDatabase(DB_FILE)

    print("\n" + "=" * 60)
    print("  AGX Central FL — Property Intelligence System")
    print("=" * 60)

    if demo:
        run_demo(db)
        do_score = True  # Always score after loading demo
    elif not any([do_discover, do_permits, do_appraiser, do_sunbiz, do_score, do_dashboard]):
        print("\n  Usage:")
        print("    python run.py --demo                  Demo with sample data")
        print("    python run.py --full --key KEY         Full scan")
        print("    python run.py --discover --key KEY     Discovery + reviews")
        print("    python run.py --permits                Permit scan (Selenium)")
        print("    python run.py --appraiser              Appraiser scan (Selenium)")
        print("    python run.py --sunbiz                 Sunbiz lookup (Selenium)")
        print("    python run.py --score                  Re-score properties")
        print("    python run.py --dashboard              Regenerate dashboard")
        print()
        return

    # Run selected modules
    if do_discover:
        from modules.discovery import discover_properties
        discover_properties(api_key, db)
        # Auto-run review analysis after discovery
        from modules.reviews import scan_all_reviews
        scan_all_reviews(db)

    if do_permits:
        from modules.permits import scan_all_permits
        scan_all_permits(db)

    if do_appraiser:
        from modules.appraiser import scan_all_appraisers
        scan_all_appraisers(db)

    if do_sunbiz:
        from modules.sunbiz import scan_all_entities
        scan_all_entities(db)

    if do_score:
        from modules.scorer import score_all_properties
        score_all_properties(db)

    # Save database
    db.save()

    if do_dashboard:
        from modules.dashboard import generate_dashboard
        output = str(project_root / OUTPUT_FILE)
        generate_dashboard(db, output)

    print("\n  🏁 All done!\n")


if __name__ == "__main__":
    main()
