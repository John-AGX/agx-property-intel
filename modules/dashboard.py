"""
AGX Property Intelligence — Dashboard Generator

Generates an interactive HTML dashboard with full property profiles:
- Lead score with breakdown
- Property details (year built, units, owner)
- Permit history timeline
- Review issues
- Corporate entity info
- Contact details

Branded with AGX green theme.
"""

from datetime import datetime
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import REVIEW_ISSUE_CATEGORIES, ROOF_AGE_ALERT_YEARS, PAINT_AGE_ALERT_YEARS


def generate_dashboard(db, output_path="lead_dashboard.html"):
    """Generate the full property intelligence dashboard."""

    properties = db.get_all()
    # Sort by lead score descending
    properties.sort(key=lambda x: x.get("lead_score", 0), reverse=True)

    stats = db.get_stats()
    hot = sum(1 for p in properties if p.get("priority") == "hot")
    warm = sum(1 for p in properties if p.get("priority") == "warm")

    # Count permit alerts
    overdue_roof = 0
    overdue_paint = 0
    for p in properties:
        from modules.permits import years_since
        if p.get("last_roof_permit"):
            yrs = years_since(p["last_roof_permit"])
            if yrs and yrs > ROOF_AGE_ALERT_YEARS:
                overdue_roof += 1
        if p.get("last_paint_permit"):
            yrs = years_since(p["last_paint_permit"])
            if yrs and yrs > PAINT_AGE_ALERT_YEARS:
                overdue_paint += 1

    # Build property cards
    cards_html = ""
    for prop in properties:
        cards_html += build_property_card(prop)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AGX Central FL — Property Intelligence Dashboard</title>
<style>
{DASHBOARD_CSS}
</style>
</head>
<body>

<div class="header">
    <div class="header-top">
        <div>
            <img src="https://agxco.com/wp-content/uploads/2025/05/agx-header-2.png" alt="AG Exteriors" class="header-logo" onerror="this.style.display='none'">
            <h1>Property Intelligence Dashboard</h1>
            <p class="subtitle">Multifamily Complex Profiles · Central Florida · 7 Counties</p>
        </div>
        <div class="generated-date">
            Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br>
            Database: {stats['total_properties']} properties
        </div>
    </div>
    <div class="stats-bar">
        <div class="stat">
            <div class="stat-value">{stats['total_properties']}</div>
            <div class="stat-label">Properties Tracked</div>
        </div>
        <div class="stat">
            <div class="stat-value hot">{hot}</div>
            <div class="stat-label">Hot Leads</div>
        </div>
        <div class="stat">
            <div class="stat-value warm">{warm}</div>
            <div class="stat-label">Warm Leads</div>
        </div>
        <div class="stat">
            <div class="stat-value">{stats['with_reviews']}</div>
            <div class="stat-label">With Review Issues</div>
        </div>
        <div class="stat">
            <div class="stat-value">{stats['with_permits']}</div>
            <div class="stat-label">With Permit Data</div>
        </div>
        <div class="stat">
            <div class="stat-value alert">{overdue_roof}</div>
            <div class="stat-label">Overdue Roofs</div>
        </div>
    </div>
</div>

<div class="controls">
    <input type="text" class="search-box" placeholder="Search by name, address, owner, issue..." oninput="filterLeads()">
    <select class="sort-select" onchange="sortLeads(this.value)">
        <option value="score-desc">Sort: Lead Score (High → Low)</option>
        <option value="score-asc">Sort: Lead Score (Low → High)</option>
        <option value="rating-asc">Sort: Rating (Worst First)</option>
        <option value="age-desc">Sort: Building Age (Oldest First)</option>
        <option value="units-desc">Sort: Units (Largest First)</option>
    </select>
    <select class="sort-select" onchange="filterPriority(this.value)">
        <option value="all">Filter: All Leads</option>
        <option value="hot">🔥 Hot Only</option>
        <option value="warm">🟡 Warm Only</option>
        <option value="cold">🔵 Cold Only</option>
    </select>
</div>

<div class="leads-container" id="leadsContainer">
    {cards_html}
</div>

<script>
{DASHBOARD_JS}
</script>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  📊 Dashboard saved to: {output_path}")
    print(f"     {stats['total_properties']} properties | {hot} hot | {warm} warm")


def build_property_card(prop):
    """Build the HTML for a single property card."""
    name = prop.get("name", "Unknown Property")
    address = prop.get("address", "")
    county = prop.get("county", "unknown").title()
    score = prop.get("lead_score", 0)
    priority = prop.get("priority", "cold")
    breakdown = prop.get("score_breakdown", {})
    rating = prop.get("google_rating")
    total_reviews = prop.get("total_reviews", 0)
    phone = prop.get("phone", "")
    website = prop.get("website", "")
    google_url = prop.get("google_url", "")

    # Owner info
    owner = prop.get("owner_info", {})
    owner_name = owner.get("owner_name", "")
    year_built = owner.get("year_built")
    units = owner.get("units")
    buildings = owner.get("buildings")
    sqft = owner.get("total_sqft")
    assessed = owner.get("assessed_value")
    parcel = owner.get("parcel_id", "")

    # Corporate info
    corp = prop.get("corporate_info", {})
    entity_name = corp.get("entity_name", "")
    agent = corp.get("registered_agent", "")
    entity_status = corp.get("status", "")
    officers = corp.get("officers", [])

    # Permits
    permits = prop.get("permits", [])
    last_roof = prop.get("last_roof_permit")
    last_paint = prop.get("last_paint_permit")

    # Review issues
    issues = prop.get("review_issues", [])

    # Priority styling
    priority_class = {"hot": "priority-hot", "warm": "priority-warm", "cold": "priority-cold"}.get(priority, "priority-cold")
    priority_label = {"hot": "🔥 HOT", "warm": "🟡 WARM", "cold": "🔵 COLD"}.get(priority, "COLD")

    # Score bar segments
    score_bar = ""
    for key, label, color in [
        ("reviews", "Reviews", "#ef4444"),
        ("permits", "Permits", "#f59e0b"),
        ("building_age", "Age", "#8b5cf6"),
        ("property_size", "Size", "#3b82f6"),
        ("reachability", "Reach", "#00d084"),
    ]:
        val = breakdown.get(key, 0)
        if val > 0:
            score_bar += f'<div class="score-segment" style="flex:{val};background:{color}" title="{label}: {val}"></div>'

    # Rating display
    rating_html = ""
    if rating:
        stars = "★" * int(rating) + ("½" if rating % 1 >= 0.5 else "") + "☆" * (5 - int(rating) - (1 if rating % 1 >= 0.5 else 0))
        rating_html = f'<span class="rating-display">{stars}</span> {rating}/5 ({total_reviews} reviews)'

    # Property details section
    details_items = []
    if year_built:
        age = datetime.now().year - year_built
        details_items.append(f"<strong>Built:</strong> {year_built} ({age} yrs old)")
    if units:
        details_items.append(f"<strong>Units:</strong> {units}")
    if buildings:
        details_items.append(f"<strong>Buildings:</strong> {buildings}")
    if sqft:
        details_items.append(f"<strong>Sq Ft:</strong> {sqft:,}")
    if assessed:
        details_items.append(f"<strong>Assessed:</strong> ${assessed:,.0f}")
    if parcel:
        details_items.append(f"<strong>Parcel:</strong> {parcel}")

    details_html = " · ".join(details_items) if details_items else "<em>No appraiser data yet</em>"

    # Owner / Corporate section
    owner_html = ""
    if owner_name or entity_name:
        owner_parts = []
        if owner_name:
            owner_parts.append(f"<strong>Owner:</strong> {owner_name}")
        if entity_name and entity_name != owner_name:
            owner_parts.append(f"<strong>Entity:</strong> {entity_name}")
        if entity_status:
            status_color = "#00d084" if entity_status.lower() == "active" else "#ef4444"
            owner_parts.append(f'<span style="color:{status_color}">({entity_status})</span>')
        if agent:
            owner_parts.append(f"<strong>Agent:</strong> {agent}")
        if officers:
            top_officers = [f"{o.get('title','')}: {o.get('name','')}" for o in officers[:3]]
            owner_parts.append(f"<strong>Officers:</strong> {', '.join(top_officers)}")
        owner_html = " · ".join(owner_parts)
    else:
        owner_html = "<em>No owner data yet</em>"

    # Permit timeline
    permit_html = ""
    if last_roof or last_paint or permits:
        permit_items = []
        if last_roof:
            from modules.permits import years_since
            yrs = years_since(last_roof)
            alert = " 🔴" if yrs and yrs > ROOF_AGE_ALERT_YEARS else ""
            permit_items.append(f"<strong>Last Roof:</strong> {last_roof} ({yrs or '?'}yr ago){alert}")
        if last_paint:
            from modules.permits import years_since
            yrs = years_since(last_paint)
            alert = " 🔴" if yrs and yrs > PAINT_AGE_ALERT_YEARS else ""
            permit_items.append(f"<strong>Last Paint:</strong> {last_paint} ({yrs or '?'}yr ago){alert}")
        if permits:
            permit_items.append(f"<strong>Total Permits:</strong> {len(permits)}")
        permit_html = " · ".join(permit_items)
    else:
        permit_html = "<em>No permit data yet</em>"

    # Review issues
    issues_html = ""
    if issues:
        for issue in sorted(issues, key=lambda x: x.get("severity", 0), reverse=True)[:8]:
            stars = "★" * issue.get("rating", 1) + "☆" * (5 - issue.get("rating", 1))
            issues_html += f"""
                <div class="issue-item" data-category="{issue.get('category','')}">
                    <div class="issue-header">
                        <span class="issue-category">{issue.get('icon','')} {issue.get('category','')}</span>
                        <span class="issue-severity">Severity: {issue.get('severity', 0)}</span>
                    </div>
                    <div class="issue-review">
                        <span class="review-stars">{stars}</span>
                        <span class="review-author">{issue.get('author','')}</span>
                        <span class="review-time">{issue.get('time','')}</span>
                    </div>
                    <p class="issue-excerpt">"{issue.get('excerpt','')}"</p>
                </div>
            """

    # Contact links
    contact_parts = []
    if phone:
        contact_parts.append(f'<a href="tel:{phone}" class="contact-link">📞 {phone}</a>')
    if website:
        contact_parts.append(f'<a href="{website}" target="_blank" class="contact-link">🌐 Website</a>')
    if google_url:
        contact_parts.append(f'<a href="{google_url}" target="_blank" class="contact-link">📍 Google Maps</a>')
    contact_html = " ".join(contact_parts) if contact_parts else ""

    # Build data attributes for filtering/sorting
    data_attrs = (
        f'data-score="{score}" '
        f'data-rating="{rating or 5}" '
        f'data-priority="{priority}" '
        f'data-county="{county}" '
        f'data-units="{units or 0}" '
        f'data-age="{datetime.now().year - year_built if year_built else 0}"'
    )

    return f"""
    <div class="lead-card {priority_class}" {data_attrs}>
        <div class="lead-header">
            <div class="lead-title-section">
                <div class="lead-name-row">
                    <h3 class="lead-name">{name}</h3>
                    <span class="priority-badge {priority_class}">{priority_label}</span>
                </div>
                <p class="lead-address">{address} · {county} County</p>
                {f'<p class="lead-rating">{rating_html}</p>' if rating_html else ''}
            </div>
            <div class="lead-score-section">
                <div class="lead-score">{score}</div>
                <div class="lead-score-label">LEAD SCORE</div>
                <div class="score-bar">{score_bar}</div>
            </div>
        </div>

        <div class="profile-sections">
            <div class="profile-section">
                <div class="section-label">🏢 Property Details</div>
                <div class="section-content">{details_html}</div>
            </div>

            <div class="profile-section">
                <div class="section-label">👤 Owner / Management</div>
                <div class="section-content">{owner_html}</div>
            </div>

            <div class="profile-section">
                <div class="section-label">📋 Permit History</div>
                <div class="section-content">{permit_html}</div>
            </div>

            {f'<div class="profile-section"><div class="section-label">📞 Contact</div><div class="section-content">{contact_html}</div></div>' if contact_html else ''}
        </div>

        {'<div class="issues-section"><button class="toggle-issues" onclick="toggleIssues(this)">▼ Show ' + str(len(issues)) + ' Flagged Review(s)</button><div class="issues-list" style="display:none;">' + issues_html + '</div></div>' if issues else ''}
    </div>
    """


# ─────────────────────────────────────────────────────────────
#  CSS & JS
# ─────────────────────────────────────────────────────────────

DASHBOARD_CSS = """
:root {
    --bg: #0b1a10;
    --card-bg: #112118;
    --card-border: #1e3a28;
    --accent: #1b8541;
    --accent-light: #00d084;
    --accent-dim: #145a2e;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --red: #ef4444;
    --orange: #f59e0b;
    --blue: #3b82f6;
    --purple: #8b5cf6;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
}

.header {
    background: linear-gradient(135deg, #0f2818 0%, #071a0d 100%);
    border-bottom: 2px solid var(--accent);
    padding: 2rem 2rem 1.5rem;
}

.header-logo { height: 50px; margin-bottom: 0.8rem; }

.header-top {
    display: flex; justify-content: space-between;
    align-items: flex-start; margin-bottom: 1.5rem;
}

.header h1 { font-size: 1.8rem; font-weight: 700; color: var(--accent-light); }
.header .subtitle { color: var(--text-dim); font-size: 0.95rem; margin-top: 0.3rem; }
.generated-date { color: var(--text-dim); font-size: 0.85rem; text-align: right; }

.stats-bar { display: flex; gap: 2rem; flex-wrap: wrap; }
.stat { text-align: center; }
.stat-value { font-size: 2rem; font-weight: 700; color: var(--accent-light); line-height: 1; }
.stat-value.hot { color: var(--red); }
.stat-value.warm { color: var(--orange); }
.stat-value.alert { color: var(--red); }
.stat-label { font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.3rem; }

.controls {
    padding: 1.2rem 2rem; background: #0d1f14;
    border-bottom: 1px solid var(--card-border);
    display: flex; flex-wrap: wrap; gap: 1rem; align-items: center;
}

.search-box {
    flex: 1; min-width: 250px; padding: 0.6rem 1rem;
    background: var(--card-bg); border: 1px solid var(--card-border);
    border-radius: 8px; color: var(--text); font-size: 0.9rem; outline: none;
}
.search-box:focus { border-color: var(--accent-light); }

.sort-select {
    padding: 0.6rem 1rem; background: var(--card-bg);
    border: 1px solid var(--card-border); border-radius: 8px;
    color: var(--text); font-size: 0.9rem; cursor: pointer;
}

.leads-container { padding: 1.5rem 2rem; max-width: 1200px; margin: 0 auto; }

.lead-card {
    background: var(--card-bg); border: 1px solid var(--card-border);
    border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;
    transition: border-color 0.2s, transform 0.2s;
    border-left: 4px solid var(--card-border);
}
.lead-card:hover { transform: translateY(-1px); }
.lead-card.priority-hot { border-left-color: var(--red); }
.lead-card.priority-warm { border-left-color: var(--orange); }
.lead-card.priority-cold { border-left-color: var(--blue); }

.lead-header {
    display: flex; justify-content: space-between;
    align-items: flex-start; margin-bottom: 1rem;
}

.lead-name-row { display: flex; align-items: center; gap: 0.8rem; }
.lead-name { font-size: 1.2rem; font-weight: 600; }
.lead-address { color: var(--text-dim); font-size: 0.85rem; margin-top: 0.2rem; }
.lead-rating { font-size: 0.85rem; margin-top: 0.3rem; color: var(--text-dim); }
.rating-display { color: var(--orange); }

.priority-badge {
    padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.7rem;
    font-weight: 600; letter-spacing: 0.05em;
}
.priority-badge.priority-hot { background: rgba(239,68,68,0.2); color: var(--red); }
.priority-badge.priority-warm { background: rgba(245,158,11,0.2); color: var(--orange); }
.priority-badge.priority-cold { background: rgba(59,130,246,0.2); color: var(--blue); }

.lead-score-section { text-align: center; flex-shrink: 0; }
.lead-score { font-size: 2rem; font-weight: 800; color: var(--accent-light); line-height: 1; }
.lead-score-label { font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.2rem; }

.score-bar {
    display: flex; height: 4px; border-radius: 2px; overflow: hidden;
    margin-top: 0.5rem; width: 80px; background: rgba(255,255,255,0.1);
}
.score-segment { min-width: 2px; }

.profile-sections {
    display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem;
    margin-bottom: 0.8rem;
}

.profile-section {
    padding: 0.6rem 0.8rem; background: rgba(0,0,0,0.2);
    border-radius: 6px; font-size: 0.82rem; line-height: 1.5;
}

.section-label {
    font-weight: 600; color: var(--accent-light); font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.3rem;
}

.section-content { color: var(--text-dim); }
.section-content strong { color: var(--text); font-weight: 500; }
.section-content em { color: var(--text-dim); opacity: 0.6; }

.contact-link {
    color: var(--accent-light); text-decoration: none; margin-right: 1rem;
}
.contact-link:hover { text-decoration: underline; }

.toggle-issues {
    background: none; border: 1px solid var(--card-border);
    color: var(--text-dim); padding: 0.5rem 1rem; border-radius: 6px;
    cursor: pointer; font-size: 0.85rem; width: 100%; text-align: left;
}
.toggle-issues:hover { border-color: var(--accent); color: var(--text); }

.issues-list { margin-top: 0.8rem; }
.issue-item {
    background: rgba(0,0,0,0.2); border-radius: 8px; padding: 1rem;
    margin-bottom: 0.5rem; border-left: 3px solid var(--accent-light);
}
.issue-header { display: flex; justify-content: space-between; margin-bottom: 0.4rem; }
.issue-category { font-weight: 600; font-size: 0.85rem; color: var(--accent-light); }
.issue-severity { font-size: 0.8rem; color: var(--red); font-weight: 500; }
.issue-review { display: flex; gap: 0.8rem; font-size: 0.8rem; color: var(--text-dim); margin-bottom: 0.4rem; }
.review-stars { color: var(--orange); }
.issue-excerpt { font-size: 0.85rem; color: var(--text); font-style: italic; line-height: 1.5; opacity: 0.9; }

@media (max-width: 768px) {
    .header { padding: 1.2rem; }
    .header h1 { font-size: 1.3rem; }
    .profile-sections { grid-template-columns: 1fr; }
    .leads-container { padding: 1rem; }
    .lead-header { flex-direction: column; }
}
"""

DASHBOARD_JS = """
let activePriority = 'all';

function filterLeads() {
    const search = document.querySelector('.search-box').value.toLowerCase();
    const cards = document.querySelectorAll('.lead-card');
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        const priority = card.dataset.priority;
        const matchesSearch = !search || text.includes(search);
        const matchesPriority = activePriority === 'all' || priority === activePriority;
        card.style.display = (matchesSearch && matchesPriority) ? 'block' : 'none';
    });
}

function filterPriority(value) {
    activePriority = value;
    filterLeads();
}

function sortLeads(criterion) {
    const container = document.getElementById('leadsContainer');
    const cards = Array.from(container.querySelectorAll('.lead-card'));
    cards.sort((a, b) => {
        switch(criterion) {
            case 'score-desc': return parseFloat(b.dataset.score) - parseFloat(a.dataset.score);
            case 'score-asc': return parseFloat(a.dataset.score) - parseFloat(b.dataset.score);
            case 'rating-asc': return parseFloat(a.dataset.rating) - parseFloat(b.dataset.rating);
            case 'age-desc': return parseInt(b.dataset.age) - parseInt(a.dataset.age);
            case 'units-desc': return parseInt(b.dataset.units) - parseInt(a.dataset.units);
        }
    });
    cards.forEach(card => container.appendChild(card));
}

function toggleIssues(btn) {
    const list = btn.nextElementSibling;
    if (list.style.display === 'none') {
        list.style.display = 'block';
        btn.textContent = btn.textContent.replace('▼ Show', '▲ Hide');
    } else {
        list.style.display = 'none';
        btn.textContent = btn.textContent.replace('▲ Hide', '▼ Show');
    }
}
"""
