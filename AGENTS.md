# Scouted / travel_app

When working in this repo with Hermes:

- Travel DB path: `data/places.json`
- Ingest skill: `kol-travel-ingest` (see `hermes-skill/kol-travel-ingest/SKILL.md`)
- Prefer chunked extraction for local Gemma4; always run `validate_places.py` after merges
- Do not invent coordinates; use the `maps` skill to geocode
