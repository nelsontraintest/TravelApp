# Entity extraction reference for Gemma4

## Allowed `type` values

`restaurant` | `cafe` | `shop` | `street` | `mall` | `attraction` | `hotel` | `person` | `product` | `other`

## Confidence guide

| Score | Meaning |
|------|---------|
| 0.9–1.0 | Exact proper name + clear location context |
| 0.6–0.8 | Named place, city/area uncertain |
| 0.3–0.5 | Nickname / partial name / on-screen only guess |
| < 0.3 | Skip (do not emit) |

## Deduping

Same `name` + same `city` → one record. Keep earliest timestamp; merge tags/aliases.

## Names (localized)

Capture local names when spoken or shown on screen:

- `names.primary` — the local/native name (日本語 for Japan, 繁體中文 for HK/TW)
- `names.en` — English name
- `names.ja` — Japanese name (if place is in Japan or has Japanese signage)
- `names.zh-Hant` — Traditional Chinese name (if spoken/shown in 繁體中文)

Keep `name` as the display default (usually English or romanized). The `names` object is optional — fill what you know from the transcript.

## Example (restaurant)

```json
{
  "type": "restaurant",
  "name": "Kumagera",
  "names": {
    "primary": "くまげら",
    "en": "Kumagera",
    "ja": "くまげら",
    "zh-Hant": ""
  },
  "aliases": ["くまげら"],
  "description": "Local Furano restaurant known for venison and mountain hot pot.",
  "tags": ["furano", "restaurant", "hot-pot", "hokkaido", "japan"],
  "source": {
    "youtube_url": "https://youtu.be/6fL9aDhAlzs",
    "youtube_title": "北海道 冬日鐵道之旅",
    "kol_id": "maibaru_travel",
    "timestamp_sec": 120,
    "quote": "在地料理店「くまげら」 紅肉是鹿肉 還有鴨肉和雞肉"
  },
  "location": {
    "lat": null,
    "lng": null,
    "address": "",
    "city": "Furano",
    "country": "JP",
    "area": "Furano"
  },
  "contact": { "phone": "", "website": "" },
  "enrichment": { "rating": null, "photos": [], "maps_url": "" },
  "confidence": 0.95,
  "needs_review": true,
  "origin": "kol"
}
```

## Example (person)

```json
{
  "type": "person",
  "name": "Example Designer",
  "aliases": [],
  "description": "Local designer introduced while visiting a boutique.",
  "tags": ["designer", "fashion"],
  "source": {
    "youtube_url": "https://www.youtube.com/watch?v=EXAMPLE",
    "youtube_title": "HK shopping",
    "kol_id": "example_kol",
    "timestamp_sec": 600,
    "quote": "This collection is by Example Designer"
  },
  "location": {
    "lat": null,
    "lng": null,
    "address": "",
    "city": "Hong Kong",
    "country": "HK",
    "area": ""
  },
  "person": {
    "role": "designer",
    "bio": "",
    "related_places": ["boutique name if mentioned"]
  },
  "confidence": 0.7,
  "needs_review": true,
  "origin": "kol"
}
```
