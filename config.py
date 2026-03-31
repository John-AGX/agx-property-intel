"""
AGX Property Intelligence — Configuration
"""
import os

# ─────────────────────────────────────────────────────────────
#  API KEYS (set via environment variables or edit here)
# ─────────────────────────────────────────────────────────────

GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

# Future paid API keys (leave blank to use free county scraping)
SHOVELS_API_KEY = os.environ.get("SHOVELS_API_KEY", "")       # shovels.ai permit data
TAXNET_API_KEY = os.environ.get("TAXNET_API_KEY", "")         # taxnetusa.com property data

# ─────────────────────────────────────────────────────────────
#  SEARCH REGIONS — Central FL (7 counties)
# ─────────────────────────────────────────────────────────────

COUNTIES = {
    "orange": {
        "name": "Orange County",
        "appraiser_url": "https://www.ocpafl.org/",
        "appraiser_search": "https://ocpaweb.ocpafl.org",
        "permits_url": "https://fasttrack.ocfl.net/OnlineServices/",
        "permit_system": "fasttrack",
    },
    "seminole": {
        "name": "Seminole County",
        "appraiser_url": "https://scpafl.org/",
        "appraiser_search": "https://www.scpafl.org/search/parcels",
        "permits_url": "https://semc-egov.aspgov.com/Click2GovBP/index.html",
        "permit_system": "click2gov",
    },
    "osceola": {
        "name": "Osceola County",
        "appraiser_url": "https://www.property-appraiser.org/",
        "appraiser_search": "https://search.property-appraiser.org/",
        "permits_url": "https://permits.osceola.org/CitizenAccess/Cap/CapHome.aspx?module=Building",
        "permit_system": "accela",
    },
    "polk": {
        "name": "Polk County",
        "appraiser_url": "https://www.polkflpa.gov/",
        "appraiser_search": "https://esearch.polkcad.org/",
        "permits_url": "https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx?module=Building",
        "permit_system": "accela",
    },
    "brevard": {
        "name": "Brevard County",
        "appraiser_url": "https://www.bcpao.us/",
        "appraiser_search": "https://www.bcpao.us/propertysearch/",
        "permits_url": "https://acaweb.brevardcounty.us/CitizenAccess/Cap/CapHome.aspx?module=Building",
        "permit_system": "accela",
    },
    "volusia": {
        "name": "Volusia County",
        "appraiser_url": "https://vcpa.vcgov.org/",
        "appraiser_search": "https://vcpa.vcgov.org/search/real-property",
        "permits_url": "https://connectlivepermits.org/",
        "permit_system": "connectlive",
    },
    "lake": {
        "name": "Lake County",
        "appraiser_url": "https://www.lakecopropappr.com/",
        "appraiser_search": "https://gis.lakecountyfl.gov/gisweb/",
        "permits_url": "https://aca-prod.accela.com/LAKECO/Default.aspx",
        "permit_system": "accela",
    },
}

# Search areas for Google Places discovery (lat, lng, radius_meters)
SEARCH_AREAS = [
    # Orange County
    {"name": "Orlando",           "lat": 28.5383, "lng": -81.3792, "radius": 30000, "county": "orange"},
    {"name": "Winter Park",       "lat": 28.5999, "lng": -81.3392, "radius": 10000, "county": "orange"},
    {"name": "Apopka",            "lat": 28.6934, "lng": -81.5312, "radius": 15000, "county": "orange"},
    # Seminole County
    {"name": "Sanford",           "lat": 28.8003, "lng": -81.2731, "radius": 20000, "county": "seminole"},
    {"name": "Altamonte Springs", "lat": 28.6611, "lng": -81.3656, "radius": 15000, "county": "seminole"},
    {"name": "Casselberry",       "lat": 28.6578, "lng": -81.3278, "radius": 10000, "county": "seminole"},
    # Osceola County
    {"name": "Kissimmee",         "lat": 28.2920, "lng": -81.4076, "radius": 20000, "county": "osceola"},
    {"name": "St. Cloud",         "lat": 28.2489, "lng": -81.2812, "radius": 15000, "county": "osceola"},
    # Polk County
    {"name": "Lakeland",          "lat": 28.0395, "lng": -81.9498, "radius": 25000, "county": "polk"},
    {"name": "Winter Haven",      "lat": 28.0222, "lng": -81.7329, "radius": 15000, "county": "polk"},
    # Brevard County
    {"name": "Melbourne",         "lat": 28.0836, "lng": -80.6081, "radius": 20000, "county": "brevard"},
    {"name": "Palm Bay",          "lat": 28.0345, "lng": -80.5887, "radius": 15000, "county": "brevard"},
    {"name": "Cocoa",             "lat": 28.3861, "lng": -80.7420, "radius": 15000, "county": "brevard"},
    # Volusia County
    {"name": "Daytona Beach",     "lat": 29.2108, "lng": -81.0228, "radius": 20000, "county": "volusia"},
    {"name": "Deltona",           "lat": 28.9005, "lng": -81.2637, "radius": 15000, "county": "volusia"},
    {"name": "Port Orange",       "lat": 29.1383, "lng": -80.9956, "radius": 12000, "county": "volusia"},
    # Lake County
    {"name": "Clermont",          "lat": 28.5494, "lng": -81.7729, "radius": 20000, "county": "lake"},
    {"name": "Leesburg",          "lat": 28.8108, "lng": -81.8779, "radius": 15000, "county": "lake"},
]

# Search queries to find apartment complexes
SEARCH_QUERIES = [
    "apartment complex",
    "multifamily apartments",
    "apartment community",
    "residential apartments",
    "senior living apartments",
]

# ─────────────────────────────────────────────────────────────
#  FILTERING THRESHOLDS
# ─────────────────────────────────────────────────────────────

MIN_REVIEWS = 10                # Minimum Google reviews to include
MAX_STAR_RATING = 4.5           # Include properties at or below this rating
ROOF_AGE_ALERT_YEARS = 15       # Flag if last roof permit > N years ago
PAINT_AGE_ALERT_YEARS = 8       # Flag if last paint permit > N years ago
BUILDING_AGE_ALERT_YEARS = 25   # Flag if building > N years old with no recent work

# ─────────────────────────────────────────────────────────────
#  PERMIT KEYWORDS — what we're looking for
# ─────────────────────────────────────────────────────────────

PERMIT_CATEGORIES = {
    "roofing": {
        "keywords": ["roof", "roofing", "re-roof", "reroof", "shingle", "roof replacement", "roof repair"],
        "priority": "high",
    },
    "painting": {
        "keywords": ["paint", "painting", "exterior paint", "repaint", "coating"],
        "priority": "high",
    },
    "stucco_siding": {
        "keywords": ["stucco", "siding", "exterior wall", "facade", "cladding", "hardie"],
        "priority": "medium",
    },
    "paving": {
        "keywords": ["paving", "asphalt", "parking lot", "resurfac", "sealcoat", "striping"],
        "priority": "medium",
    },
    "structural": {
        "keywords": ["structural", "foundation", "concrete repair", "load bearing", "balcony"],
        "priority": "high",
    },
    "waterproofing": {
        "keywords": ["waterproof", "water intrusion", "moisture", "sealant", "membrane", "flashing"],
        "priority": "medium",
    },
}

# ─────────────────────────────────────────────────────────────
#  ISSUE KEYWORDS — for Google Review analysis
# ─────────────────────────────────────────────────────────────

REVIEW_ISSUE_CATEGORIES = {
    "Roofing & Water Intrusion": {
        "keywords": [
            r"roof\s*leak", r"leaking\s*roof", r"roof\s*damage", r"roof\s*repair",
            r"water\s*damage", r"water\s*intrusion", r"water\s*leak",
            r"ceiling\s*leak", r"leak.*ceiling", r"dripping",
            r"rain.*inside", r"rain.*coming\s*in", r"water\s*stain",
            r"roof\s*cave", r"roof\s*coll?aps", r"shingle", r"tarps?\s*on\s*roof",
            r"water\s*pour", r"flood.*rain", r"roof\s*rot",
        ],
        "severity_boost": 1.5,
        "icon": "🏚️",
    },
    "Foundation & Structural": {
        "keywords": [
            r"foundation", r"structur", r"crack.*wall", r"wall.*crack",
            r"sinking", r"settling", r"load.?bearing", r"support\s*beam",
            r"concrete\s*crack", r"concrete\s*damage", r"slab",
            r"floor.*uneven", r"uneven.*floor", r"lean", r"tilt",
            r"building.*shift", r"structural\s*damage", r"unsafe.*building",
            r"building.*unsafe", r"condemn",
        ],
        "severity_boost": 1.3,
        "icon": "🏗️",
    },
    "Siding & Stucco": {
        "keywords": [
            r"siding", r"stucco", r"exterior\s*wall", r"facade",
            r"paint.*peel", r"peel.*paint", r"exterior.*paint",
            r"wood\s*rot", r"rot.*wood", r"rot.*soding",
            r"caulk", r"seal", r"weather.*strip", r"drafty",
            r"exterior.*damage", r"exterior.*falling", r"falling.*apart",
            r"crumbl", r"deteriorat",
        ],
        "severity_boost": 1.0,
        "icon": "🧱",
    },
    "Parking & Paving": {
        "keywords": [
            r"parking\s*lot", r"pothole", r"asphalt", r"paving",
            r"parking.*damage", r"parking.*crack", r"parking.*terrible",
            r"speed\s*bump", r"curb", r"parking\s*garage",
            r"concrete.*parking", r"resurface", r"repav",
            r"park.*flood", r"drain.*parking", r"lot.*flood",
        ],
        "severity_boost": 0.8,
        "icon": "🅿️",
    },
    "Mold & Moisture": {
        "keywords": [
            r"mold", r"mildew", r"moisture", r"damp",
            r"black\s*mold", r"mold.*ceiling", r"mold.*wall",
            r"musty", r"humid", r"condensat",
            r"mold.*everywhere", r"mold.*health", r"toxic.*mold",
        ],
        "severity_boost": 1.2,
        "icon": "🦠",
    },
    "General Exterior Neglect": {
        "keywords": [
            r"maintenance.*terrible", r"maintenance.*awful", r"maintenance.*worst",
            r"never\s*fix", r"won?t\s*fix", r"refuse.*fix", r"refuse.*repair",
            r"falling\s*apart", r"run\s*down", r"dilapidated", r"neglect",
            r"eyesore", r"condemned", r"slum", r"hazard",
            r"code\s*violation", r"fail.*inspection", r"inspection.*fail",
            r"years.*without\s*repair", r"defer.*maintenance",
        ],
        "severity_boost": 1.1,
        "icon": "⚠️",
    },
}

# ─────────────────────────────────────────────────────────────
#  SYSTEM
# ─────────────────────────────────────────────────────────────

API_DELAY = 0.3                 # Seconds between API calls
SELENIUM_TIMEOUT = 15           # Browser automation timeout
DATA_DIR = "data"               # Local data storage
DB_FILE = "data/properties.json"
OUTPUT_FILE = "lead_dashboard.html"
