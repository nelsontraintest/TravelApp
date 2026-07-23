#!/usr/bin/env python3
"""Enrich places with OSM data: geocode, phone, website, local names, maps_url.

Usage:
    python3 enrich_places.py <extract.json>         # enrich extracted places
    python3 enrich_places.py --db                    # re-enrich all places in places.json
    python3 enrich_places.py --db --missing-only     # only fill places missing maps_url / coords

Outputs enriched JSON to stdout (or overwrites places.json with --db --in-place).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
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

PLACE_LIKE_TYPES = frozenset({
    "restaurant", "cafe", "shop", "street", "mall", "attraction", "hotel",
})


def _request(url: str) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        # macOS Python often lacks certs; fall back to curl which uses system CA store
        try:
            raw = subprocess.check_output(
                ["curl", "-sL", "-A", USER_AGENT, "--max-time", "15", url],
                stderr=subprocess.DEVNULL,
            )
            return json.loads(raw)
        except (subprocess.CalledProcessError, OSError, json.JSONDecodeError):
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


def maps_url_coords(lat: float, lng: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"


def maps_url_text(name: str, city: str = "", area: str = "") -> str:
    parts = [p for p in (name, area, city) if p]
    query = ", ".join(parts) if parts else name
    return (
        "https://www.google.com/maps/search/?api=1&query="
        + urllib.parse.quote(query)
    )


def _short_name_variants(name: str) -> list[str]:
    """Drop parentheticals and trailing location qualifiers for shorter queries."""
    variants: list[str] = []
    if not name:
        return variants
    no_paren = re.sub(r"\s*\([^)]*\)\s*", " ", name).strip()
    no_paren = re.sub(r"\s+", " ", no_paren)
    if no_paren and no_paren != name:
        variants.append(no_paren)
    # First segment before an em/en dash or " - "
    for sep in (" — ", " – ", " - "):
        if sep in name:
            head = name.split(sep, 1)[0].strip()
            if head and head != name:
                variants.append(head)
            break
    return variants


def geocode_queries(place: dict) -> list[str]:
    """Build ordered Nominatim query strings; first hit wins."""
    loc = place.get("location") or {}
    names = place.get("names") or {}
    name = (place.get("name") or "").strip()
    city = (loc.get("city") or "").strip()
    area = (loc.get("area") or "").strip()
    if not name or not city:
        return []

    seen: set[str] = set()
    queries: list[str] = []

    def add(q: str) -> None:
        q = re.sub(r"\s+", " ", q).strip()
        if q and q not in seen:
            seen.add(q)
            queries.append(q)

    add(f"{name}, {city}")
    ja = (names.get("ja") or "").strip()
    if ja:
        add(f"{ja}, {city}")
    primary = (names.get("primary") or "").strip()
    if primary and primary != name and primary != ja:
        add(f"{primary}, {city}")
    for alias in place.get("aliases") or []:
        a = (alias or "").strip()
        if a:
            add(f"{a}, {city}")
    if area:
        add(f"{name}, {area}, {city}")
        if ja:
            add(f"{ja}, {area}, {city}")
        # Strip area token from name (e.g. "Blue Bottle … Kiyosumi-Shirakawa")
        if area.lower() in name.lower():
            stripped = re.sub(re.escape(area), "", name, flags=re.IGNORECASE)
            stripped = re.sub(r"[\s\-–—]+", " ", stripped).strip(" -–—")
            if stripped and stripped.lower() != name.lower():
                add(f"{stripped}, {city}")
                add(f"{stripped}, {area}, {city}")
    for short in _short_name_variants(name):
        add(f"{short}, {city}")
        if area:
            add(f"{short}, {area}, {city}")
    return queries


def apply_geocode_hit(place: dict, best: dict) -> tuple[float, float]:
    loc = place.setdefault("location", {})
    enrichment = place.setdefault("enrichment", {})
    loc["lat"] = float(best["lat"])
    loc["lng"] = float(best["lon"])
    loc["address"] = best.get("display_name", "") or loc.get("address", "")
    osm_type = best.get("osm_type", "")
    osm_id_val = best.get("osm_id", "")
    if osm_type and osm_id_val:
        enrichment["osm_url"] = f"https://www.openstreetmap.org/{osm_type}/{osm_id_val}"
    enrichment["maps_url"] = maps_url_coords(loc["lat"], loc["lng"])
    enrichment["source"] = "osm"
    enrichment["geocode_status"] = "resolved"
    return loc["lat"], loc["lng"]


def apply_maps_search_fallback(place: dict) -> None:
    """No coords — still provide a useful Maps text search + missing flag."""
    loc = place.get("location") or {}
    enrichment = place.setdefault("enrichment", {})
    name = (place.get("name") or "").strip()
    city = (loc.get("city") or "").strip()
    area = (loc.get("area") or "").strip()
    if name:
        enrichment["maps_url"] = maps_url_text(name, city, area)
        enrichment["source"] = "maps_search"
    enrichment["geocode_status"] = "missing"
    if place.get("type") in PLACE_LIKE_TYPES:
        place["needs_review"] = True


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
    tried_geocode = False

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
        tried_geocode = True
        for query in geocode_queries(place):
            print(f"    geocode try: {query}", file=sys.stderr)
            results = nominatim_search(query)
            time.sleep(RATE_LIMIT)
            if results:
                best = results[0]
                lat, lng = apply_geocode_hit(place, best)
                osm_data = best
                print(f"    geocode hit: {query}", file=sys.stderr)
                break
    elif lat is not None and not osm_data:
        # We have coords but no osm detail; try search by name+city for extra tags
        if name and city:
            results = nominatim_search(f"{name}, {city}")
            time.sleep(RATE_LIMIT)
            if results:
                osm_data = results[0]

    # Refresh lat/lng from location after possible geocode
    loc = place.get("location") or loc
    lat = loc.get("lat")
    lng = loc.get("lng")

    if lat is not None and lng is not None:
        enrichment["maps_url"] = maps_url_coords(lat, lng)
        if enrichment.get("source") != "osm":
            enrichment["source"] = "osm"
        enrichment["geocode_status"] = "resolved"
    elif tried_geocode or (name and city and lat is None):
        apply_maps_search_fallback(place)
    elif lat is None and lng is None:
        # person/product with no city attempt, or already unresolved
        if not enrichment.get("geocode_status"):
            enrichment["geocode_status"] = "skipped"
        if name and not enrichment.get("maps_url"):
            apply_maps_search_fallback(place)

    # Extract tags from OSM data
    if osm_data:
        extratags = osm_data.get("extratags") or {}
        namedetails = osm_data.get("namedetails") or {}

        phone = extratags.get("phone") or osm_data.get("phone", "")
        website = extratags.get("website") or osm_data.get("website", "")
        if phone and not contact.get("phone"):
            contact["phone"] = phone
        if website and not contact.get("website"):
            contact["website"] = website

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

        image = extratags.get("image") or extratags.get("wikimedia_commons", "")
        if image and not enrichment.get("photos"):
            if image.startswith("http"):
                enrichment["photos"] = [image]
            elif image.startswith("File:"):
                wiki_name = urllib.parse.quote(image.replace("File:", ""))
                enrichment["photos"] = [
                    f"https://commons.wikimedia.org/wiki/Special:FilePath/{wiki_name}"
                ]

    # Don't overwrite source when maps_search fallback already set
    if lat is not None and lng is not None:
        enrichment["source"] = "osm"
    elif enrichment.get("source") not in ("maps_search", "osm", "google_places"):
        enrichment["source"] = enrichment.get("source") or "osm"

    place["enrichment"] = enrichment
    place["contact"] = contact
    place["location"] = loc
    return place


def _needs_missing_enrich(place: dict) -> bool:
    """True if place should be re-enriched under --missing-only."""
    loc = place.get("location") or {}
    enr = place.get("enrichment") or {}
    if loc.get("lat") is None or loc.get("lng") is None:
        return True
    if not enr.get("maps_url"):
        return True
    if enr.get("geocode_status") == "missing":
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Enrich places with OSM data")
    parser.add_argument("input", nargs="?", help="Extract JSON file to enrich")
    parser.add_argument("--db", action="store_true", help="Enrich places in places.json")
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Only enrich places missing coords, maps_url, or geocode_status=missing",
    )
    parser.add_argument("--in-place", action="store_true", help="Write back to places.json (with --db)")
    args = parser.parse_args()

    if args.db:
        db = json.loads(PLACES_JSON.read_text(encoding="utf-8"))
        places = db.get("places", [])
        count = 0
        for place in places:
            if args.missing_only and not _needs_missing_enrich(place):
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
