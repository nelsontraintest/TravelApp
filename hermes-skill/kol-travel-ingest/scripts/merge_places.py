#!/usr/bin/env python3
"""Merge extracted place objects into data/places.json (dedupe by id / name+city)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return s[:48] or "place"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalize_incoming(raw) -> list[dict]:
    if isinstance(raw, dict):
        if "places" in raw:
            return list(raw["places"])
        return [raw]
    if isinstance(raw, list):
        return list(raw)
    raise SystemExit("Incoming JSON must be a place object, list of places, or {places: [...]}")


def ensure_id(place: dict) -> dict:
    if place.get("id"):
        return place
    city = (place.get("location") or {}).get("city") or "unknown"
    place["id"] = f"{slugify(city)}_{slugify(place.get('name', 'unnamed'))}"
    return place


def find_existing(db_places: list[dict], place: dict) -> int | None:
    pid = place.get("id")
    if pid:
        for i, existing in enumerate(db_places):
            if existing.get("id") == pid:
                return i
    name = (place.get("name") or "").strip().lower()
    city = ((place.get("location") or {}).get("city") or "").strip().lower()
    if not name:
        return None
    for i, existing in enumerate(db_places):
        ename = (existing.get("name") or "").strip().lower()
        ecity = ((existing.get("location") or {}).get("city") or "").strip().lower()
        if ename == name and (not city or not ecity or city == ecity):
            return i
    return None


def deep_merge(base: dict, incoming: dict) -> dict:
    out = dict(base)
    for key, value in incoming.items():
        if value in (None, "", [], {}):
            continue
        if key in ("location", "contact", "enrichment", "person", "source") and isinstance(value, dict):
            merged = dict(out.get(key) or {})
            for sk, sv in value.items():
                if sv not in (None, "", [], {}):
                    merged[sk] = sv
            out[key] = merged
        elif key == "tags" and isinstance(value, list):
            tags = list(out.get("tags") or [])
            for t in value:
                if t not in tags:
                    tags.append(t)
            out[key] = tags
        elif key == "aliases" and isinstance(value, list):
            aliases = list(out.get("aliases") or [])
            for a in value:
                if a not in aliases:
                    aliases.append(a)
            out[key] = aliases
        else:
            out[key] = value
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge extracted places into places.json")
    parser.add_argument("incoming", help="JSON file with one place, a list, or {places: [...]}")
    parser.add_argument(
        "--db",
        default=None,
        help="Path to places.json (default: <repo>/data/places.json)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[3]
    db_path = Path(args.db) if args.db else repo / "data" / "places.json"
    incoming_path = Path(args.incoming)

    db = load_json(db_path)
    places = list(db.get("places") or [])
    incoming = [ensure_id(p) for p in normalize_incoming(load_json(incoming_path))]

    added, updated = 0, 0
    for place in incoming:
        place.setdefault("origin", "kol")
        place.setdefault("needs_review", True)
        place.setdefault("confidence", 0.6)
        idx = find_existing(places, place)
        if idx is None:
            places.append(place)
            added += 1
        else:
            places[idx] = deep_merge(places[idx], place)
            updated += 1

    db["places"] = places
    db["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    db.setdefault("version", 1)

    print(json.dumps({"added": added, "updated": updated, "total": len(places)}, indent=2))
    if not args.dry_run:
        save_json(db_path, db)
        print(f"Wrote {db_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
