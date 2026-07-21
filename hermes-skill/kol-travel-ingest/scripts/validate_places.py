#!/usr/bin/env python3
"""Validate places.json shape for travel_app travel DB."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_PLACE = ("id", "type", "name", "source")
REQUIRED_DEMO_PIN = ("id", "label", "lat", "lng")
ALLOWED_TYPES = {
    "restaurant",
    "cafe",
    "shop",
    "street",
    "mall",
    "attraction",
    "hotel",
    "person",
    "product",
    "other",
}


def validate(db: dict) -> list[str]:
    errors: list[str] = []
    if "places" not in db or not isinstance(db["places"], list):
        return ["missing places array"]

    ids: set[str] = set()
    for i, place in enumerate(db["places"]):
        prefix = f"places[{i}]"
        if not isinstance(place, dict):
            errors.append(f"{prefix}: not an object")
            continue
        for key in REQUIRED_PLACE:
            if key not in place:
                errors.append(f"{prefix}: missing {key}")
        pid = place.get("id")
        if pid:
            if pid in ids:
                errors.append(f"{prefix}: duplicate id {pid}")
            ids.add(pid)
        ptype = place.get("type")
        if ptype and ptype not in ALLOWED_TYPES:
            errors.append(f"{prefix}: invalid type {ptype}")
        source = place.get("source") or {}
        if isinstance(source, dict) and "kol_id" not in source:
            errors.append(f"{prefix}: source.kol_id required")
        loc = place.get("location") or {}
        if isinstance(loc, dict):
            lat, lng = loc.get("lat"), loc.get("lng")
            if (lat is None) ^ (lng is None):
                errors.append(f"{prefix}: lat/lng must both be set or both null")
        names = place.get("names")
        if names is not None and not isinstance(names, dict):
            errors.append(f"{prefix}: names must be an object")
        enrichment = place.get("enrichment") or {}
        if isinstance(enrichment, dict):
            maps_url = enrichment.get("maps_url")
            if maps_url and not maps_url.startswith("http"):
                errors.append(f"{prefix}: enrichment.maps_url must be a URL")
            for photo_url in (enrichment.get("photos") or []):
                if photo_url and not photo_url.startswith("http"):
                    errors.append(f"{prefix}: enrichment.photos contains non-URL")
                    break
        contact = place.get("contact") or {}
        if isinstance(contact, dict):
            website = contact.get("website")
            if website and not website.startswith("http"):
                errors.append(f"{prefix}: contact.website must be a URL")

    demo_pins = db.get("demo_pins")
    if demo_pins is not None:
        if not isinstance(demo_pins, list):
            errors.append("demo_pins must be an array")
        else:
            pin_ids: set[str] = set()
            for i, pin in enumerate(demo_pins):
                prefix = f"demo_pins[{i}]"
                if not isinstance(pin, dict):
                    errors.append(f"{prefix}: not an object")
                    continue
                for key in REQUIRED_DEMO_PIN:
                    if key not in pin:
                        errors.append(f"{prefix}: missing {key}")
                pid = pin.get("id")
                if pid:
                    if pid in pin_ids:
                        errors.append(f"{prefix}: duplicate id {pid}")
                    pin_ids.add(pid)
                for coord in ("lat", "lng"):
                    val = pin.get(coord)
                    if val is not None and not isinstance(val, (int, float)):
                        errors.append(f"{prefix}: {coord} must be a number")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to places.json",
    )
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    path = Path(args.path) if args.path else repo / "data" / "places.json"
    db = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(db)
    if errors:
        print("INVALID", file=sys.stderr)
        for e in errors:
            print(f" - {e}", file=sys.stderr)
        sys.exit(1)
    demo_count = len(db.get("demo_pins") or [])
    print(
        json.dumps(
            {"ok": True, "places": len(db["places"]), "demo_pins": demo_count, "path": str(path)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
