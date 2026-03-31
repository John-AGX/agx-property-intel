# AGX Property Intelligence

**Lead generation system for AG Exteriors (Central Florida) — multifamily apartment complex property profiling and scoring.**

Automatically discovers, profiles, and ranks large multifamily apartment complexes across 7 Central Florida counties based on exterior & structural maintenance needs.

## What It Does

| Module | Source | Data |
|--------|--------|------|
| Discovery | Google Places API | Find apartment complexes across Central FL |
| Review Analysis | Google Reviews | Flag tenant complaints about roofing, foundation, stucco, parking, mold |
| Permit History | County portals (Selenium) or Shovels.ai API | Last roof permit, last paint, structural work dates |
| Property Appraiser | County portals (Selenium) | Owner name, year built, units, assessed value |
| Corporate Lookup | Florida Sunbiz | Management company, registered agent, officers |
| Lead Scoring | All sources combined | 0-100 score → Hot / Warm / Cold priority |

## Counties Covered

Orange · Seminole · Osceola · Polk · Brevard · Volusia · Lake

## Quick Start

```bash
# Demo mode (no API keys needed)
python run.py --demo

# Full scan with Google Places API key
python run.py --full --key YOUR_GOOGLE_API_KEY

# Individual modules
python run.py --discover --key KEY    # Find properties + scan reviews
python run.py --permits               # Scan county permit databases
python run.py --appraiser             # Scrape property appraiser data
python run.py --sunbiz                # Look up corporate entities
python run.py --score                 # Re-score all properties
python run.py --dashboard             # Regenerate dashboard
```

## Requirements

- Python 3.8+
- Google Places API key (free $200/mo credit) — for discovery
- Selenium + ChromeDriver — for free county portal scraping
- OR Shovels.ai API key — for paid permit data

## Lead Scoring

Each property scored on 5 dimensions (100 pts max):

| Component | Points | What It Measures |
|-----------|--------|------------------|
| Reviews | 0-40 | Tenant complaints about exterior/structural issues |
| Permits | 0-30 | How overdue for roof/paint/structural work |
| Building Age | 0-10 | Older buildings = more maintenance needs |
| Property Size | 0-10 | Larger properties = bigger potential jobs |
| Reachability | 0-10 | Contact info, owner data, agent info available |

**Priority:** 🔥 HOT (60+) · 🟡 WARM (35-59) · 🔵 COLD (<35)

## Output

Interactive HTML dashboard with full property profiles, filterable and sortable. AGX branded.

## License

Private — AG Exteriors internal use.
