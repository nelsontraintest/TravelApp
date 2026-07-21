# travel_app

Personal travel web app: pull places from travel KOL YouTube videos with **Hermes + local Gemma4**, store them in `data/places.json`, then open the site on your **iPhone** to see what’s nearby and swipe likes.

**Live app (GitHub Pages):**  
**https://nelsontraintest.github.io/TravelApp/web/**

Repo: [nelsontraintest/TravelApp](https://github.com/nelsontraintest/TravelApp)

---

## How to open the app

### On iPhone (recommended — real GPS works)

1. Open Safari (not in-app browsers if location fails).
2. Go to: **https://nelsontraintest.github.io/TravelApp/web/**
3. Tap **Use my location** → **Allow**.
4. Pick a **Radius** (start with 1–5 km).
5. If nothing is in range → you’ll see **No travel spots nearby** (expected until you ingest places near you, or use a larger radius / Demo pin).

**Why HTTPS?** iPhone Safari blocks GPS on plain `http://` LAN IPs. GitHub Pages gives HTTPS, so location works.

Optional: add to Home Screen (Share → Add to Home Screen).

### On Mac (same live site)

Open the same URL in any browser:  
https://nelsontraintest.github.io/TravelApp/web/

### Local Mac server (optional, for development)

```bash
cd /path/to/TravelApp   # or your local clone
./scripts/serve.sh
```

Then open `http://127.0.0.1:8765/web/` on the Mac.

- GPS works on Mac localhost.
- On iPhone over hotspot/LAN HTTP, GPS is usually **blocked** — use **Demo pin**, or open the **GitHub Pages HTTPS** link instead.

---

## App features

| Tab | What it does |
|-----|----------------|
| **Nearby** | Uses your location (or Demo pin / `?lat=&lng=`) and lists places within the radius |
| **Swipe** | Like / Nope on KOL places; likes stay on that phone (`localStorage`) |

- Cards from videos are labeled **From KOL video**.
- Suggestions from your taste are labeled **From your likes (not KOL)**.

### Demo pins

If you’re not near the seed data (Hong Kong / Tokyo samples), choose **Demo pin → HK Central** to see example results.

### Optional iPhone Shortcut

1. Shortcuts → New Shortcut  
2. Get **Current Location**  
3. Open URL:  
   `https://nelsontraintest.github.io/TravelApp/web/index.html?lat=LATITUDE&lng=LONGITUDE`  
   (replace with Shortcut location variables)

---

## Project layout

| Path | Purpose |
|------|---------|
| `data/places.json` | Travel database (commit this after Hermes ingest) |
| `data/schema.json` | Record shape |
| `web/` | Nearby + Swipe UI |
| `hermes-skill/kol-travel-ingest/` | Hermes skill: YouTube → extract → geocode → merge |
| `scripts/serve.sh` | Local static server |
| `AGENTS.md` | Short notes for Hermes when working in this repo |

---

## Operate with Hermes + Gemma4 (ingest videos)

You run **Gemma4 via Hermes/Ollama** on your Mac. Hermes fills `data/places.json`; the website only reads that file (no local model on the phone).

### One-time setup

1. Clone this repo (or use your existing local folder that matches this project).
2. Install the skill into Hermes:

```bash
mkdir -p ~/.hermes/skills/media
ln -sfn "$(pwd)/hermes-skill/kol-travel-ingest" ~/.hermes/skills/media/kol-travel-ingest
```

3. Confirm Ollama + Gemma4 are running (`hermes` model already points at local Gemma4).
4. Start a **new** Hermes session: `hermes`

### Ingest one YouTube video

Paste into Hermes:

```text
Use skill kol-travel-ingest.
Ingest this YouTube video into my travel_app travel DB:
<PASTE_YOUTUBE_URL>
KOL name: <NAME>
City/region hint: Hong Kong
```

Hermes will:

1. Fetch the transcript (`youtube-content`)
2. Extract restaurants / shops / streets / people / products (Gemma4 → JSON)
3. Geocode with the **maps** skill (OpenStreetMap)
4. Merge into `data/places.json` and validate

### Publish new places to the live iPhone app

After a good ingest:

```bash
cd /path/to/TravelApp
git add data/places.json
git commit -m "Add places from <KOL / video title>"
git push origin main
```

Wait 1–2 minutes for GitHub Pages to update, then reload Safari on the iPhone.

### Manual merge / validate

```bash
python3 hermes-skill/kol-travel-ingest/scripts/merge_places.py /tmp/travel_app/extract_xxx.json
python3 hermes-skill/kol-travel-ingest/scripts/validate_places.py
```

More detail: `hermes-skill/kol-travel-ingest/SKILL.md`

---

## Update the live site after code changes

```bash
git add -A
git commit -m "Describe your change"
git push origin main
```

GitHub Pages deploys from the `main` branch (site root). Live URL stays:

https://nelsontraintest.github.io/TravelApp/web/

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| iPhone: “origin does not have permission to use Geolocation” on LAN HTTP | Use the **GitHub Pages https://** link above |
| No spots nearby | Larger radius, Demo pin, or ingest places near your city |
| Pages 404 after push | Wait a minute; confirm Pages is on for `main` / root |
| Hermes skill not found | Re-run the `ln -sfn` symlink; start a **new** Hermes chat |
| Transcript empty | Video may have captions disabled; Hermes skill will stop rather than invent places |

---

## Beginner checklist

- [ ] Open https://nelsontraintest.github.io/TravelApp/web/ on iPhone
- [ ] Allow location (or use Demo pin HK Central)
- [ ] Try **Swipe**, then return to **Nearby**
- [ ] Symlink Hermes skill and ingest one KOL video
- [ ] `git push` updated `data/places.json` and reload the phone

---

## Optional later

- Google Places API for phone / reviews / photos (cache into `places.json`)
- Google Sheet as a human review UI synced to JSON
