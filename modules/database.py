"""
AGX Property Intelligence — JSON Database Manager

Stores and manages property profiles as a local JSON database.
Each property is keyed by a normalized address hash for deduplication.
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path


class PropertyDatabase:
    """Manages the local property intelligence database."""

    def __init__(self, db_path="data/properties.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.properties = {}
        self.metadata = {
            "created": datetime.now().isoformat(),
            "last_updated": None,
            "total_scans": 0,
            "version": "1.0",
        }
        self.load()

    def load(self):
        """Load database from disk."""
        if self.db_path.exists():
            with open(self.db_path, "r") as f:
                data = json.load(f)
                self.properties = data.get("properties", {})
                self.metadata = data.get("metadata", self.metadata)
            print(f"  📂 Loaded {len(self.properties)} properties from database")
        else:
            print(f"  📂 Starting fresh database at {self.db_path}")

    def save(self):
        """Save database to disk."""
        self.metadata["last_updated"] = datetime.now().isoformat()
        data = {
            "metadata": self.metadata,
            "properties": self.properties,
        }
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  💾 Saved {len(self.properties)} properties to {self.db_path}")

    @staticmethod
    def make_key(address):
        """Generate a stable key from an address for deduplication."""
        normalized = address.lower().strip()
        for prefix in ["apt ", "unit ", "suite ", "#", "ste "]:
            idx = normalized.find(prefix)
            if idx > 0:
                normalized = normalized[:idx].strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def get(self, address):
        """Get a property by address."""
        key = self.make_key(address)
        return self.properties.get(key)

    def upsert(self, address, data):
        """Insert or update a property profile."""
        key = self.make_key(address)
        if key in self.properties:
            existing = self.properties[key]
            for field, value in data.items():
                if value is not None and value != "" and value != []:
                    if isinstance(value, dict) and isinstance(existing.get(field), dict):
                        existing[field].update(value)
                    elif isinstance(value, list) and isinstance(existing.get(field), list):
                        existing_set = {json.dumps(i, sort_keys=True, default=str) for i in existing[field]}
                        for item in value:
                            item_key = json.dumps(item, sort_keys=True, default=str)
                            if item_key not in existing_set:
                                existing[field].append(item)
                    else:
                        existing[field] = value
            existing["last_updated"] = datetime.now().isoformat()
        else:
            data["first_seen"] = datetime.now().isoformat()
            data["last_updated"] = datetime.now().isoformat()
            self.properties[key] = data
        return key

    def get_all(self):
        """Get all properties as a list."""
        return list(self.properties.values())

    def get_by_county(self, county):
        """Get properties in a specific county."""
        return [p for p in self.properties.values() if p.get("county") == county]

    def count(self):
        """Return total number of properties."""
        return len(self.properties)

    def get_stats(self):
        """Get summary statistics."""
        props = self.get_all()
        counties = set(p.get("county", "unknown") for p in props)
        with_permits = sum(1 for p in props if p.get("permits"))
        with_reviews = sum(1 for p in props if p.get("review_issues"))
        with_owner = sum(1 for p in props if p.get("owner_info"))
        scored = [p for p in props if p.get("lead_score", 0) > 0]

        return {
            "total_properties": len(props),
            "counties": len(counties),
            "with_permits": with_permits,
            "with_reviews": with_reviews,
            "with_owner_info": with_owner,
            "scored_leads": len(scored),
            "top_score": max((p.get("lead_score", 0) for p in props), default=0),
        }

    def new_property_template(self, name, address, county=""):
        """Create a blank property profile template."""
        return {
            "name": name,
            "address": address,
            "county": county,
            "place_id": "",
            "google_url": "",
            "phone": "",
            "website": "",
            "google_rating": None,
            "total_reviews": 0,
            "review_issues": [],
            "review_scan_date": None,
            "owner_info": {
                "owner_name": "",
                "mailing_address": "",
                "year_built": None,
                "units": None,
                "buildings": None,
                "total_sqft": None,
                "assessed_value": None,
                "land_use": "",
                "parcel_id": "",
            },
            "appraiser_scan_date": None,
            "permits": [],
            "last_roof_permit": None,
            "last_paint_permit": None,
            "last_structural_permit": None,
            "permit_scan_date": None,
            "corporate_info": {
                "entity_name": "",
                "entity_type": "",
                "status": "",
                "registered_agent": "",
                "agent_address": "",
                "filing_date": "",
                "officers": [],
            },
            "sunbiz_scan_date": None,
            "lead_score": 0,
            "score_breakdown": {},
            "priority": "",
            "notes": "",
            "first_seen": None,
            "last_updated": None,
        }
