---
name: kol-travel-ingest
description: "Extract restaurants, shops, streets, malls, people, and products from travel KOL YouTube videos into Scouted places.json. Use when the user pastes a YouTube URL, asks to ingest a travel vlog, build a travel database, or enrich place names with maps/geocoding."
version: 1.0.0
author: Scouted / travel_app
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [youtube, travel, kol, places, ingest, gemma, scouted]
    related_skills: [youtube-content, maps]
    requires_toolsets: [terminal]
---

# KOL Travel Ingest (Scouted)

## Overview

Turn a travel KOL YouTube video into structured places for the **Scouted** web app
(`travel_app/data/places.json`). Optimized for **local Gemma4** via Hermes:
short steps, strict JSON, and helper scripts — avoid huge single prompts.

## When to Use

- User pastes a YouTube travel/vlog URL and wants places extracted
- User says: ingest video, build travel DB, scrape KOL mentions, enrich restaurants
- User wants to append results into `data/places.json`

Don't use for: general YouTube summaries (use `youtube-content`), or live "near me" queries (that's the web app).

## Project paths

Assume the Scouted repo is:

```text
TRAVEL_APP=/Users/nlee/DevelopmentProjects/projects/travel_app
SKILL_DIR=$TRAVEL_APP/hermes-skill/kol-travel-ingest
YT_SCRIPT=~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py
MAPS=~/.hermes/skills/productivity/maps/scripts/maps_client.py
```

If `TRAVEL_APP` differs, ask once and remember for the session.

## Workflow (follow in order)

### 1. Fetch transcript

```bash
uv pip install youtube-transcript-api
uv run python3 "$YT_SCRIPT" "YOUTUBE_URL" --timestamps --language zh-Hans,zh-Hant,zh,en,ja,ko
```

Completion criteria: non-empty `full_text` / timestamped output. If empty, retry without `--language`. If still empty, tell the user transcripts are disabled and stop (do not invent places).

### 2. Extract entities with Gemma (you)

From the transcript, list every **concrete** mention:

| type | examples |
|------|----------|
| restaurant / cafe | named eateries |
| shop / mall / product | stores, malls, products, brands |
| street / attraction / hotel | streets, landmarks, hotels |
| person | designers, chefs, hosts named on screen or spoken |

Ignore: filler, ads with no place name, vague "a cafe nearby" without a name.

Output **only** a JSON array (no markdown fences) matching:

```json
[
  {
    "type": "restaurant",
    "name": "Exact Name",
    "aliases": [],
    "description": "one short sentence from context",
    "tags": ["city-or-area", "food-type"],
    "source": {
      "youtube_url": "FULL_URL",
      "youtube_title": "",
      "kol_id": "kol_slug",
      "timestamp_sec": 123,
      "quote": "short quote from transcript"
    },
    "location": {
      "lat": null,
      "lng": null,
      "address": "",
      "city": "City if known",
      "country": "",
      "area": "district if known"
    },
    "contact": { "phone": "", "website": "" },
    "enrichment": { "rating": null, "photos": [] },
    "confidence": 0.7,
    "needs_review": true,
    "origin": "kol"
  }
]
```

For people, also allow:

```json
"person": { "role": "designer", "bio": "", "related_places": [] }
```

Gemma tips (local model):

- Work in chunks if transcript is long (~8–12k chars per pass), then merge/dedupe by name+city
- Prefer lower `confidence` when the name is unclear
- Set `needs_review: true` unless the name is crystal clear
- Never invent lat/lng — leave null until maps enrichment

Write the array to a temp file:

```bash
mkdir -p /tmp/scouted
# save extraction as /tmp/scouted/extract_<videoid>.json
```

### 3. Enrich with maps (geocode)

For each place with a usable name + city/area (skip vague / person-only without place):

```bash
python3 "$MAPS" search "NAME, CITY"
```

If a clear hit exists, fill `location.lat`, `location.lng`, `location.address`, and set `enrichment.osm_url` if available. Do **not** overwrite a good human address with a worse one.

Rate-limit: pause ~1s between Nominatim searches. Completion criteria: every high-confidence restaurant/cafe/shop/mall/attraction either has coords or an explicit note why geocode failed.

Optional later: Google Places API for phone/reviews/photos — not required for MVP. Prefer maps skill first (no API key).

### 4. Merge into the database

```bash
python3 "$SKILL_DIR/scripts/merge_places.py" /tmp/scouted/extract_<videoid>.json
python3 "$SKILL_DIR/scripts/validate_places.py"
```

Completion criteria: validate prints `"ok": true`. Summarize for the user: added / updated counts, list of names, which still `needs_review`.

### 5. Tell the user how to see results

```bash
cd "$TRAVEL_APP" && ./scripts/serve.sh
```

Open the URL on iPhone (same Wi‑Fi) → **Nearby** or **Swipe**.

## One-shot user prompt (copy for beginners)

```text
Use skill kol-travel-ingest.
Ingest this YouTube video into my Scouted travel DB:
<PASTE_URL>
KOL name: <NAME>
City/region hint: <e.g. Hong Kong / Tokyo>
```

## Common pitfalls

1. **Inventing places** from vibes — only extract named entities.
2. **Skipping timestamps** — always set `timestamp_sec` when possible.
3. **Geocoding without city** — add region hint from video title/description.
4. **One giant prompt** — chunk for Gemma4; merge JSON after.
5. **Forgetting validate** — always run `validate_places.py` after merge.

## Verification checklist

- [ ] Transcript fetched successfully
- [ ] Extraction JSON saved under `/tmp/scouted/`
- [ ] Maps enrichment attempted for place-like types
- [ ] `merge_places.py` reported added/updated
- [ ] `validate_places.py` ok
- [ ] User told how to refresh the web app
