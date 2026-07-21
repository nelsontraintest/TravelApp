#!/usr/bin/env python3
"""Validate places.json shape for travel_app travel DB."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_PLACE = ("id", "type", "name", "source")
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
    print(json.dumps({"ok": True, "places": len(db["places"]), "path": str(path)}, indent=2))


if __name__ == "__main__":
    main()
