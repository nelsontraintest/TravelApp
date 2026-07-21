#!/usr/bin/env python3
"""Merge extracted place objects into data/places.json (dedupe by id / name+city)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LIVE_APP_BASE = "https://nelsontraintest.github.io/TravelApp/web/index.html"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return s[:48] or "place"


def pin_id_for_city(city: str) -> str:
    return slugify(city).replace("_", "-")[:48]


def preview_url(lat: float, lng: float) -> str:
    return f"{LIVE_APP_BASE}?lat={lat:.4f}&lng={lng:.4f}"


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


def _coords(place: dict) -> tuple[float, float] | None:
    loc = place.get("location") or {}
    lat, lng = loc.get("lat"), loc.get("lng")
    if lat is None or lng is None:
        return None
    try:
        return float(lat), float(lng)
    except (TypeError, ValueError):
        return None


def _city_key(place: dict) -> str | None:
    loc = place.get("location") or {}
    city = (loc.get("city") or loc.get("area") or "").strip()
    return city or None


def _pin_label(city: str, country: str, area: str, tags: list[str]) -> str:
    tag_set = {t.lower() for t in tags}
    if "hokkaido" in tag_set and city:
        return f"{city}, Hokkaido"
    if country in ("HK", "Hong Kong"):
        if city and city.lower() not in ("hong kong", "hk"):
            return f"HK {city}"
        return city or "Hong Kong"
    if area and area != city:
        return f"{city}, {area}"
    return city


def upsert_demo_pins(db: dict, incoming: list[dict]) -> list[str]:
    """Create/update demo_pins from geocoded places in the incoming batch."""
    by_city: dict[str, list[dict]] = defaultdict(list)
    for place in incoming:
        coords = _coords(place)
        city = _city_key(place)
        if coords and city:
            by_city[city].append(place)

    pins = list(db.get("demo_pins") or [])
    pin_index = {p["id"]: i for i, p in enumerate(pins) if p.get("id")}
    updated_labels: list[str] = []

    for city, group in by_city.items():
        lats, lngs = [], []
        for p in group:
            c = _coords(p)
            if c:
                lats.append(c[0])
                lngs.append(c[1])
        if not lats:
            continue

        lat = round(sum(lats) / len(lats), 4)
        lng = round(sum(lngs) / len(lngs), 4)
        sample = group[0]
        loc = sample.get("location") or {}
        country = loc.get("country") or ""
        area = loc.get("area") or ""
        source = sample.get("source") or {}
        all_tags: list[str] = []
        for p in group:
            all_tags.extend(p.get("tags") or [])
        pid = pin_id_for_city(city)
        label = _pin_label(city, country, area, all_tags)

        pin = {
            "id": pid,
            "label": label,
            "lat": lat,
            "lng": lng,
            "city": city,
            "country": country,
            "preview_url": preview_url(lat, lng),
        }
        yt = source.get("youtube_url")
        if yt:
            pin["source_youtube_url"] = yt

        if pid in pin_index:
            pins[pin_index[pid]] = {**pins[pin_index[pid]], **pin}
        else:
            pins.append(pin)
            pin_index[pid] = len(pins) - 1
        updated_labels.append(label)

    db["demo_pins"] = pins
    return updated_labels


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
    pin_labels = upsert_demo_pins(db, incoming)
    db["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    db.setdefault("version", 1)

    result = {
        "added": added,
        "updated": updated,
        "total": len(places),
        "demo_pins_updated": pin_labels,
    }
    print(json.dumps(result, indent=2))
    if not args.dry_run:
        save_json(db_path, db)
        print(f"Wrote {db_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
