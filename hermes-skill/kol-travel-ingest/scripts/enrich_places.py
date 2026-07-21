#!/usr/bin/env python3
"""Enrich places with OSM data: geocode, phone, website, local names, maps_url.

Usage:
    python3 enrich_places.py <extract.json>         # enrich extracted places
    python3 enrich_places.py --db                    # re-enrich all places in places.json
    python3 enrich_places.py --db --missing-only     # only fill places missing maps_url

Outputs enriched JSON to stdout (or overwrites places.json with --db --in-place).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PLACES_JSON = REPO / "data" / "places.json"

USER_AGENT = "TravelAppEnrich/1.0"
NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
NOMINATIM_LOOKUP = "https://nominatim.openstreetmap.org/lookup"
RATE_LIMIT = 1.1  # seconds between Nominatim requests


def _request(url: str) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        print(f"  [warn] request failed: {e}", file=sys.stderr)
        return None


def nominatim_search(query: str) -> list[dict]:
    params = urllib.parse.urlencode({
        "q": query,
        "format": "jsonv2",
        "limit": "3",
        "addressdetails": "1",
        "extratags": "1",
        "namedetails": "1",
    })
    return _request(f"{NOMINATIM_SEARCH}?{params}") or []


def nominatim_lookup(osm_type: str, osm_id: int | str) -> dict | None:
    type_prefix = {"node": "N", "way": "W", "relation": "R"}.get(osm_type, osm_type[0].upper())
    params = urllib.parse.urlencode({
        "osm_ids": f"{type_prefix}{osm_id}",
        "format": "jsonv2",
        "extratags": "1",
        "namedetails": "1",
    })
    results = _request(f"{NOMINATIM_LOOKUP}?{params}")
    if results and isinstance(results, list) and len(results) > 0:
        return results[0]
    return None


def maps_url(lat: float, lng: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"


def enrich_place(place: dict) -> dict:
    """Enrich a single place dict with OSM data. Mutates in place."""
    loc = place.get("location") or {}
    contact = place.setdefault("contact", {})
    enrichment = place.setdefault("enrichment", {})
    names = place.get("names") or {}

    lat = loc.get("lat")
    lng = loc.get("lng")
    name = place.get("name", "")
    city = loc.get("city", "")

    osm_data = None

    # If we have an osm_url, try lookup for detailed tags
    existing_osm = enrichment.get("osm_url", "")
    if existing_osm and "/node/" in existing_osm:
        osm_id = existing_osm.split("/node/")[-1]
        osm_data = nominatim_lookup("node", osm_id)
        time.sleep(RATE_LIMIT)
    elif existing_osm and "/way/" in existing_osm:
        osm_id = existing_osm.split("/way/")[-1]
        osm_data = nominatim_lookup("way", osm_id)
        time.sleep(RATE_LIMIT)
    elif lat is None and name and city:
        # Geocode
        results = nominatim_search(f"{name}, {city}")
        time.sleep(RATE_LIMIT)
        if results:
            best = results[0]
            loc["lat"] = float(best["lat"])
            loc["lng"] = float(best["lon"])
            loc["address"] = best.get("display_name", "")
            place["location"] = loc
            osm_type = best.get("osm_type", "")
            osm_id_val = best.get("osm_id", "")
            if osm_type and osm_id_val:
                enrichment["osm_url"] = f"https://www.openstreetmap.org/{osm_type}/{osm_id_val}"
            osm_data = best
            lat = loc["lat"]
            lng = loc["lng"]
    elif lat is not None and not osm_data:
        # We have coords but no osm detail; try search by name+city for extra tags
        if name and city:
            results = nominatim_search(f"{name}, {city}")
            time.sleep(RATE_LIMIT)
            if results:
                osm_data = results[0]

    # Fill maps_url
    if lat is not None and lng is not None:
        enrichment["maps_url"] = maps_url(lat, lng)

    # Extract tags from OSM data
    if osm_data:
        extratags = osm_data.get("extratags") or {}
        namedetails = osm_data.get("namedetails") or {}

        # Phone / website from extratags or top-level
        phone = extratags.get("phone") or osm_data.get("phone", "")
        website = extratags.get("website") or osm_data.get("website", "")
        if phone and not contact.get("phone"):
            contact["phone"] = phone
        if website and not contact.get("website"):
            contact["website"] = website

        # Local names
        name_ja = namedetails.get("name:ja", "")
        name_zh = namedetails.get("name:zh") or namedetails.get("name:zh-Hant", "")
        name_en = namedetails.get("name:en", "")

        if name_ja or name_zh or name_en:
            if not names:
                names = {}
            if name_ja and not names.get("ja"):
                names["ja"] = name_ja
            if name_zh and not names.get("zh-Hant"):
                names["zh-Hant"] = name_zh
            if name_en and not names.get("en"):
                names["en"] = name_en
            primary = names.get("primary") or name_ja or namedetails.get("name", "")
            if primary:
                names["primary"] = primary
            place["names"] = names

        # Wikimedia image
        image = extratags.get("image") or extratags.get("wikimedia_commons", "")
        if image and not enrichment.get("photos"):
            if image.startswith("http"):
                enrichment["photos"] = [image]
            elif image.startswith("File:"):
                wiki_name = urllib.parse.quote(image.replace("File:", ""))
                enrichment["photos"] = [
                    f"https://commons.wikimedia.org/wiki/Special:FilePath/{wiki_name}"
                ]

    enrichment["source"] = "osm"
    place["enrichment"] = enrichment
    place["contact"] = contact
    return place


def main():
    parser = argparse.ArgumentParser(description="Enrich places with OSM data")
    parser.add_argument("input", nargs="?", help="Extract JSON file to enrich")
    parser.add_argument("--db", action="store_true", help="Enrich places in places.json")
    parser.add_argument("--missing-only", action="store_true", help="Only enrich places missing maps_url")
    parser.add_argument("--in-place", action="store_true", help="Write back to places.json (with --db)")
    args = parser.parse_args()

    if args.db:
        db = json.loads(PLACES_JSON.read_text(encoding="utf-8"))
        places = db.get("places", [])
        count = 0
        for place in places:
            if args.missing_only:
                enr = place.get("enrichment") or {}
                if enr.get("maps_url"):
                    continue
            print(f"  enriching: {place.get('name', '?')}", file=sys.stderr)
            enrich_place(place)
            count += 1
        db["places"] = places
        if args.in_place:
            PLACES_JSON.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps({"enriched": count, "path": str(PLACES_JSON)}))
        else:
            print(json.dumps(db, indent=2, ensure_ascii=False))
    elif args.input:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        places = data if isinstance(data, list) else data.get("places", [data])
        count = 0
        for place in places:
            print(f"  enriching: {place.get('name', '?')}", file=sys.stderr)
            enrich_place(place)
            count += 1
        print(json.dumps(places, indent=2, ensure_ascii=False))
        print(f"\n# Enriched {count} places", file=sys.stderr)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
