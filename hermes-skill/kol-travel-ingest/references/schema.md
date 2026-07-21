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

## Example (restaurant)

```json
{
  "type": "restaurant",
  "name": "Lin Heung Tea House",
  "aliases": ["蓮香樓"],
  "description": "Old-school dim sum mentioned during Sheung Wan walk.",
  "tags": ["dim-sum", "sheung-wan", "hong-kong"],
  "source": {
    "youtube_url": "https://www.youtube.com/watch?v=EXAMPLE",
    "youtube_title": "HK food walk",
    "kol_id": "example_kol",
    "timestamp_sec": 420,
    "quote": "Let's try Lin Heung for push-cart dim sum"
  },
  "location": {
    "lat": null,
    "lng": null,
    "address": "",
    "city": "Hong Kong",
    "country": "HK",
    "area": "Sheung Wan"
  },
  "contact": { "phone": "", "website": "" },
  "enrichment": { "rating": null, "photos": [] },
  "confidence": 0.85,
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
