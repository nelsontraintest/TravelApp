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
| `data/places.json` | Travel database (commit/push after Hermes ingest) |
| `data/schema.json` | Record shape |
| `web/` | Nearby + Swipe UI |
| `hermes-skill/kol-travel-ingest/` | Hermes skill: YouTube → extract → geocode → merge → publish |
| `scripts/publish_places.sh` | Validate, commit `places.json` only, push to GitHub Pages |
| `scripts/serve.sh` | Local static server (dev) |
| `AGENTS.md` | Short notes for Hermes when working in this repo |

---

## Ingest via WhatsApp (recommended)

**Option A:** WhatsApp → Hermes extracts places → updates `data/places.json` → **git push** → GitHub Pages refreshes in about **1–2 minutes**. (Not an instant live database.)

Full detail: [`hermes-skill/kol-travel-ingest/references/whatsapp.md`](hermes-skill/kol-travel-ingest/references/whatsapp.md)

### Hermes agent: step-by-step

#### Part 1 — One-time setup (Mac)

1. Open **Terminal** (Cursor terminal or Mac Terminal).

2. Go to your local clone:

```bash
cd /Users/nlee/DevelopmentProjects/projects/travel_app
```

(Use your actual clone path if different.)

3. Link the ingest skill into Hermes:

```bash
mkdir -p ~/.hermes/skills/media
ln -sfn "$(pwd)/hermes-skill/kol-travel-ingest" ~/.hermes/skills/media/kol-travel-ingest
```

4. Confirm **Ollama + Gemma4** are running:

```bash
ollama list
```

You should see `gemma4latest-64K:latest` (or similar). Start the Ollama app if needed.

5. Pair **WhatsApp** with Hermes (QR — you must do this once):

```bash
hermes whatsapp
```

- A QR code appears in Terminal  
- On iPhone: **WhatsApp → Settings → Linked devices → Link a device**  
- Scan the QR  

6. Install and start the **Hermes gateway** (receives WhatsApp while Mac is on):

```bash
hermes gateway install
hermes gateway start
hermes gateway status
```

You want **Gateway is running**. After pairing WhatsApp, if messages don’t arrive, run `hermes gateway restart`.

7. Confirm **git push** works (Hermes uses this to publish):

```bash
git push origin main
```

#### Part 2 — Every time you ingest a video

1. Keep your Mac **awake** and check the gateway:

```bash
hermes gateway status
```

If stopped: `hermes gateway start`

2. Send a message on **WhatsApp** to Hermes:

```text
Ingest for travel_app:
https://www.youtube.com/watch?v=VIDEO_ID
KOL: <NAME>
City: Hong Kong
```

Or paste only the YouTube URL — Hermes may ask one short follow-up (KOL name or city).

3. **Wait** for Hermes to finish (can take several minutes on long videos). It will:

   - Fetch the transcript  
   - Extract places with Gemma4  
   - Geocode via the maps skill  
   - Merge into `data/places.json`  
   - Run `./scripts/publish_places.sh` (commit + push)  
   - Reply on WhatsApp with a summary  

4. On iPhone: wait **~1–2 minutes** for GitHub Pages, then reload  
   **https://nelsontraintest.github.io/TravelApp/web/**  
   and check **Nearby** (location or Demo pin).

#### What a successful Hermes reply looks like

- Added / updated place counts (brief name list)  
- Some entries may still `need_review`  
- Live app: https://nelsontraintest.github.io/TravelApp/web/  
- Reminder to wait 1–2 minutes, then reload Safari  

### One-time setup (quick reference)

Same as Part 1 above — symlink skill, Ollama/Gemma4, `hermes whatsapp`, `hermes gateway start`.

Keep your Mac on (and gateway running) when you want WhatsApp ingest to work.

### Message to send on WhatsApp

```text
Ingest for travel_app:
https://www.youtube.com/watch?v=VIDEO_ID
KOL: <NAME>
City: Hong Kong
```

Or paste only the YouTube URL — Hermes may ask one short follow-up.

### After Hermes replies

1. Wait **~1–2 minutes** for GitHub Pages.
2. Reload https://nelsontraintest.github.io/TravelApp/web/ on iPhone.
3. Check Nearby (location or Demo pin).

Hermes should run `./scripts/publish_places.sh` for you (commits **only** `data/places.json`).

---

## Operate with Hermes CLI / chat (alternate)

Same skill as WhatsApp, but you type in Terminal instead of messaging.

1. Start Hermes:

```bash
hermes
```

2. Paste:

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
5. Publish with `./scripts/publish_places.sh` (unless you ask for local-only)

### Manual merge / publish

```bash
python3 hermes-skill/kol-travel-ingest/scripts/merge_places.py /tmp/travel_app/extract_xxx.json
python3 hermes-skill/kol-travel-ingest/scripts/validate_places.py
./scripts/publish_places.sh "Add places from <KOL / video title>"
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
| Pages 404 / stale after push | Wait 1–2 minutes; hard-refresh Safari |
| WhatsApp: no Hermes reply | `hermes gateway status` → `hermes gateway start`; re-pair with `hermes whatsapp`; try `hermes gateway restart` |
| Gateway up but Hermes silent | Confirm Ollama/Gemma4 running (`ollama list`); check `hermes logs` |
| Hermes skill not found | Re-run the `ln -sfn` symlink; start a **new** Hermes session |
| Transcript empty | Video may have captions disabled; Hermes should stop rather than invent places |
| Publish / git push failed | Check `gh auth status` and that `git push origin main` works on the Mac |

---

## Beginner checklist

- [ ] Open https://nelsontraintest.github.io/TravelApp/web/ on iPhone
- [ ] Allow location (or use Demo pin HK Central)
- [ ] Try **Swipe**, then return to **Nearby**
- [ ] Symlink Hermes skill; pair WhatsApp; start gateway
- [ ] Send one YouTube URL on WhatsApp; wait for reply + Pages; reload the phone

---

## Optional later

- Live database (Option B) for near-instant updates without waiting on Pages
- Google Places API for phone / reviews / photos (cache into `places.json`)
- Google Sheet as a human review UI synced to JSON
