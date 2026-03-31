"""
AGX Property Intelligence — Lead Scoring Engine

Scores and ranks properties based on all available intelligence:
- Review issues (severity, volume, categories)
- Permit age (how long since last roof / paint / structural work)
- Building age
- Property size (larger = bigger potential job)
- Owner/management data quality (can we reach them?)
"""

from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ROOF_AGE_ALERT_YEARS, PAINT_AGE_ALERT_YEARS, BUILDING_AGE_ALERT_YEARS


def years_since_date(date_str):
    """Calculate years since a date string."""
    if not date_str:
        return None
    for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y", "%Y-%m-%dT%H:%M:%S"]:
        try:
            dt = datetime.strptime(date_str.strip()[:19], fmt)
            return round((datetime.now() - dt).days / 365.25, 1)
        except (ValueError, AttributeError):
            continue
    return None


def score_property(prop):
    """
    Calculate a comprehensive lead score for a property.

    Score components:
        1. Review Issues (0-40 pts)     — tenant complaints about exterior/structural
        2. Permit Age (0-30 pts)        — how overdue for roof/paint/structural work
        3. Building Age (0-10 pts)      — older buildings need more work
        4. Property Size (0-10 pts)     — larger properties = bigger jobs
        5. Reachability (0-10 pts)      — do we have contact info / owner data

    Total possible: ~100 pts
    """
    breakdown = {}
    total = 0.0

    # ── 1. REVIEW ISSUES (0-40 pts) ────────────────────────
    review_score = 0.0
    issues = prop.get("review_issues", [])
    if issues:
        # Sum severity scores (capped at 30)
        raw_severity = sum(i.get("severity", 0) for i in issues)
        review_score += min(raw_severity, 30)

        # Bonus for multiple issue categories (up to 10)
        unique_cats = set(i.get("category") for i in issues)
        review_score += min(len(unique_cats) * 2.5, 10)

    # Low Google rating boost
    rating = prop.get("google_rating")
    if rating and rating <= 2.5:
        review_score *= 1.3
    elif rating and rating <= 3.0:
        review_score *= 1.1

    review_score = min(review_score, 40)
    breakdown["reviews"] = round(review_score, 1)
    total += review_score

    # ── 2. PERMIT AGE (0-30 pts) ──────────────────────────
    permit_score = 0.0

    # Roof permit age
    last_roof = prop.get("last_roof_permit")
    roof_years = years_since_date(last_roof)
    if roof_years:
        if roof_years > ROOF_AGE_ALERT_YEARS + 5:
            permit_score += 15  # Way overdue
        elif roof_years > ROOF_AGE_ALERT_YEARS:
            permit_score += 10  # Overdue
        elif roof_years > 10:
            permit_score += 5   # Getting there
    elif prop.get("permit_scan_date"):
        # Scanned but no roof permit found — could be very old
        permit_score += 8

    # Paint permit age
    last_paint = prop.get("last_paint_permit")
    paint_years = years_since_date(last_paint)
    if paint_years:
        if paint_years > PAINT_AGE_ALERT_YEARS + 3:
            permit_score += 10
        elif paint_years > PAINT_AGE_ALERT_YEARS:
            permit_score += 7
        elif paint_years > 5:
            permit_score += 3
    elif prop.get("permit_scan_date"):
        permit_score += 5

    # Structural permit age
    last_struct = prop.get("last_structural_permit")
    struct_years = years_since_date(last_struct)
    if struct_years and struct_years > 20:
        permit_score += 5

    permit_score = min(permit_score, 30)
    breakdown["permits"] = round(permit_score, 1)
    total += permit_score

    # ── 3. BUILDING AGE (0-10 pts) ────────────────────────
    building_score = 0.0
    year_built = prop.get("owner_info", {}).get("year_built")
    if year_built:
        age = datetime.now().year - year_built
        if age > 40:
            building_score = 10
        elif age > BUILDING_AGE_ALERT_YEARS:
            building_score = 7
        elif age > 15:
            building_score = 4
        elif age > 10:
            building_score = 2

    breakdown["building_age"] = round(building_score, 1)
    total += building_score

    # ── 4. PROPERTY SIZE (0-10 pts) ───────────────────────
    size_score = 0.0
    units = prop.get("owner_info", {}).get("units")
    if units:
        if units > 300:
            size_score = 10
        elif units > 200:
            size_score = 8
        elif units > 100:
            size_score = 6
        elif units > 50:
            size_score = 4
        else:
            size_score = 2

    breakdown["property_size"] = round(size_score, 1)
    total += size_score

    # ── 5. REACHABILITY (0-10 pts) ────────────────────────
    reach_score = 0.0
    if prop.get("phone"):
        reach_score += 3
    if prop.get("website"):
        reach_score += 2
    if prop.get("owner_info", {}).get("owner_name"):
        reach_score += 2
    if prop.get("corporate_info", {}).get("registered_agent"):
        reach_score += 3

    breakdown["reachability"] = round(reach_score, 1)
    total += reach_score

    # ── PRIORITY LABEL ────────────────────────────────────
    if total >= 60:
        priority = "hot"
    elif total >= 35:
        priority = "warm"
    else:
        priority = "cold"

    return {
        "lead_score": round(total, 1),
        "score_breakdown": breakdown,
        "priority": priority,
    }


def score_all_properties(db):
    """
    Score and rank all properties in the database.
    """
    print("\n" + "=" * 60)
    print("  MODULE 6: Lead Scoring Engine")
    print("=" * 60)

    properties = db.get_all()
    if not properties:
        print("  No properties to score.")
        return

    hot = warm = cold = 0

    for prop in properties:
        scores = score_property(prop)
        db.upsert(prop["address"], scores)

        priority = scores["priority"]
        name = prop.get("name", "Unknown")
        score = scores["lead_score"]

        if priority == "hot":
            hot += 1
            print(f"  🔥 {name}: {score} (HOT)")
        elif priority == "warm":
            warm += 1
            print(f"  🟡 {name}: {score} (WARM)")
        else:
            cold += 1

    print(f"\n  ✅ Scored {len(properties)} properties:")
    print(f"     🔥 {hot} HOT  |  🟡 {warm} WARM  |  🔵 {cold} COLD")
