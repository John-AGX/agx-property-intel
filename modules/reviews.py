"""
AGX Property Intelligence — Review Analysis Module

Analyzes Google Reviews for exterior & structural maintenance issues.
"""

import re
import sys
from datetime import datetime

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from config import REVIEW_ISSUE_CATEGORIES


def analyze_reviews(reviews):
    """
    Analyze a list of Google reviews for exterior/structural issues.
    Returns list of issues found.
    """
    issues = []

    for review in reviews:
        text = review.get("text", "").lower()
        rating = review.get("rating", 5)
        author = review.get("author_name", "Anonymous")
        time_desc = review.get("relative_time_description", "")

        for category, config in REVIEW_ISSUE_CATEGORIES.items():
            matched_keywords = []
            for pattern in config["keywords"]:
                if re.search(pattern, text, re.IGNORECASE):
                    matched_keywords.append(pattern)

            if matched_keywords:
                severity = (5 - rating) * len(matched_keywords) * config["severity_boost"]

                # Extract relevant sentences
                sentences = re.split(r'[.!?]+', review.get("text", ""))
                relevant_excerpts = []
                for sentence in sentences:
                    for pattern in matched_keywords:
                        if re.search(pattern, sentence, re.IGNORECASE):
                            cleaned = sentence.strip()
                            if cleaned and cleaned not in relevant_excerpts:
                                relevant_excerpts.append(cleaned)
                            break

                issues.append({
                    "category": category,
                    "icon": config["icon"],
                    "severity": round(severity, 1),
                    "rating": rating,
                    "author": author,
                    "time": time_desc,
                    "excerpt": " | ".join(relevant_excerpts[:3]) if relevant_excerpts else text[:200],
                    "keyword_count": len(matched_keywords),
                })

    return issues


def scan_all_reviews(db):
    """
    Scan all properties in the database for review issues.
    Uses stored raw reviews from discovery module.
    """
    print("\n" + "=" * 60)
    print("  MODULE 2: Review Analysis")
    print("=" * 60)

    properties = db.get_all()
    scanned = 0
    flagged = 0

    for prop in properties:
        raw_reviews = prop.get("_raw_reviews", [])
        if not raw_reviews:
            continue

        issues = analyze_reviews(raw_reviews)
        if issues:
            db.upsert(prop["address"], {
                "review_issues": issues,
                "review_scan_date": datetime.now().isoformat(),
            })
            flagged += 1
            cats = set(i["category"] for i in issues)
            print(f"  🔴 {prop['name']}: {len(issues)} issues ({', '.join(cats)})")

        scanned += 1

    print(f"\n  ✅ Scanned {scanned} properties, {flagged} with maintenance issues")
    return flagged
