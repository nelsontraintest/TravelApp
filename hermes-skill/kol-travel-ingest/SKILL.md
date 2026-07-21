---
name: kol-travel-ingest
description: "Extract restaurants, shops, streets, malls, people, and products from travel KOL YouTube videos into travel_app places.json, then publish to GitHub Pages. Use when the user pastes a YouTube URL (including WhatsApp), asks to ingest a travel vlog, build a travel database, enrich place names, or update the live travel_app site."
version: 1.1.0
author: travel_app
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [youtube, travel, kol, places, ingest, gemma, travel_app, whatsapp]
    related_skills: [youtube-content, maps]
    requires_toolsets: [terminal]
---

# KOL Travel Ingest (travel_app)

## Overview

Turn a travel KOL YouTube video into structured places for the **travel_app** web app
(`data/places.json`), then **git push** so GitHub Pages updates the live iPhone site
(Option A — usually ready in 1–2 minutes after push).

Optimized for **local Gemma4** via Hermes: short steps, strict JSON, helper scripts.
WhatsApp operator details: `references/whatsapp.md`.

## When to Use

- User pastes a YouTube travel/vlog URL (CLI, chat, or **WhatsApp**)
- User says: ingest video, build travel DB, scrape KOL mentions, enrich restaurants
- User wants to append results into `data/places.json` and update the live app

Don't use for: general YouTube summaries (use `youtube-content`), or live "near me" queries (that's the web app).

## Project paths

Assume the travel_app repo is:

```text
TRAVEL_APP=/Users/nlee/DevelopmentProjects/projects/travel_app
SKILL_DIR=$TRAVEL_APP/hermes-skill/kol-travel-ingest
YT_SCRIPT=~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py
MAPS=~/.hermes/skills/productivity/maps/scripts/maps_client.py
```

If `TRAVEL_APP` differs, ask once and remember for the session.

## Workflow (follow in order)

### 0. WhatsApp / minimal prompts

If the user only sends a YouTube URL:

- Infer **KOL name** from the channel/title when possible; otherwise ask **one** short question
- Infer **city/region** from the title/description when possible; otherwise ask **one** short question
- Then continue the workflow below

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
    "names": { "primary": "日本語名", "en": "English Name", "ja": "日本語名", "zh-Hant": "繁體中文名" },
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
    "enrichment": { "rating": null, "photos": [], "maps_url": "" },
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
mkdir -p /tmp/travel_app
# save extraction as /tmp/travel_app/extract_<videoid>.json
```

### 3–5. Enrich + Merge + Validate + Publish (one command)

Instead of manually geocoding each place, run the **ingest pipeline**:

```bash
python3 "$SKILL_DIR/scripts/ingest_pipeline.py" /tmp/travel_app/extract_<videoid>.json --publish
```

This single command does:

1. **Enrich** — geocodes via OSM, fills `contact.phone`, `contact.website`, `names.ja`/`names.zh-Hant`, `enrichment.maps_url`, and photos (when OSM has them). Rate-limited 1s per request.
2. **Merge** — upserts into `data/places.json` + auto-updates `demo_pins` (one per city centroid). Prints `demo_pins_updated` with preview area labels.
3. **Validate** — checks schema. Fails if invalid.
4. **Publish** — commits only `data/places.json` and pushes to `origin/main`.

Omit `--publish` to do steps 1–3 without pushing (for local review).

Completion criteria: pipeline prints `"ok": true` from validate. Keep added/updated counts for the reply. Mention new preview areas.

**Fallback (manual steps):** if the pipeline fails, run individually:

```bash
python3 "$SKILL_DIR/scripts/enrich_places.py" /tmp/travel_app/extract_<videoid>.json > /tmp/travel_app/enriched.json
python3 "$SKILL_DIR/scripts/merge_places.py" /tmp/travel_app/enriched.json
python3 "$SKILL_DIR/scripts/validate_places.py"
./scripts/publish_places.sh "Add places from <KOL or video title>"
```

### 6. Reply to the user (WhatsApp / chat)

Send a short summary:

- Added / updated counts and place names (brief list)
- **Preview areas** added or refreshed (city labels) — user can pick them in Nearby; default radius is **All in area**
- Which still `needs_review`
- Live app: `https://nelsontraintest.github.io/TravelApp/web/`
- Tell them to **wait ~1–2 minutes**, then reload Safari on iPhone

### Dev-only: local preview

Only if the user asks to test without publishing:

```bash
cd "$TRAVEL_APP" && ./scripts/serve.sh
```

## One-shot prompts

### WhatsApp (recommended)

```text
Ingest for travel_app:
https://www.youtube.com/watch?v=VIDEO_ID
KOL: <NAME>
City: Hong Kong
```

Or just the YouTube URL — then infer or ask one clarifying question.

### Hermes CLI / chat

```text
Use skill kol-travel-ingest.
Ingest this YouTube video into my travel_app travel DB:
<PASTE_URL>
KOL name: <NAME>
City/region hint: <e.g. Hong Kong / Tokyo>
```

## Common pitfalls

1. **Inventing places** from vibes — only extract named entities.
2. **Skipping timestamps** — always set `timestamp_sec` when possible.
3. **Geocoding without city** — add region hint from video title/description.
4. **One giant prompt** — chunk for Gemma4; merge JSON after.
5. **Forgetting publish** — always run `publish_places.sh` after a successful merge (unless user said local-only).
6. **Committing extra files** — never `git add -A`; only the publish script’s `data/places.json`.

## Verification checklist

- [ ] Transcript fetched successfully
- [ ] Extraction JSON saved under `/tmp/travel_app/`
- [ ] Maps enrichment attempted for place-like types
- [ ] `merge_places.py` reported added/updated and `demo_pins_updated` if any
- [ ] `validate_places.py` ok
- [ ] `publish_places.sh` pushed successfully
- [ ] User got live URL + 1–2 min reload note
