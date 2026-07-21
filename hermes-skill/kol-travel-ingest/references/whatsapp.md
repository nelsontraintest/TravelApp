# WhatsApp ingest for travel_app (Option A)

Send a YouTube link to Hermes on WhatsApp. Hermes runs `kol-travel-ingest`, updates
`data/places.json`, and **pushes to GitHub**. The live site updates after GitHub Pages
rebuilds (~1–2 minutes). This is not an instant live database.

Live app: https://nelsontraintest.github.io/TravelApp/web/

## Prerequisites

- Mac can run Hermes + Ollama with **Gemma4**
- This repo cloned locally (example): `/Users/nlee/DevelopmentProjects/projects/travel_app`
- Skill symlink installed:

```bash
mkdir -p ~/.hermes/skills/media
ln -sfn /Users/nlee/DevelopmentProjects/projects/travel_app/hermes-skill/kol-travel-ingest \
  ~/.hermes/skills/media/kol-travel-ingest
```

- Git push to `nelsontraintest/TravelApp` works from that Mac (`git push origin main`)

## One-time WhatsApp + gateway setup

1. Pair WhatsApp with Hermes (QR code on the Mac):

```bash
hermes whatsapp
```

Scan with your phone (WhatsApp → Linked devices).

2. Install and start the messaging gateway so Hermes receives WhatsApp while the Mac is on:

```bash
hermes gateway install
hermes gateway start
hermes gateway status
```

Foreground alternative for debugging: `hermes gateway run`

3. Keep the Mac awake (or allow wake) while you expect ingest jobs. Sleeping Mac = no WhatsApp replies and no publish.

## What to send on WhatsApp

Preferred:

```text
Ingest for travel_app:
https://www.youtube.com/watch?v=VIDEO_ID
KOL: <NAME>
City: Hong Kong
```

Minimal (Hermes may ask one follow-up):

```text
https://www.youtube.com/watch?v=VIDEO_ID
```

## What Hermes should do

1. Fetch transcript  
2. Extract places with Gemma4  
3. Geocode via maps skill  
4. Merge + validate `data/places.json`  
5. Run `./scripts/publish_places.sh`  
6. Reply with counts + live URL  

## Expected reply shape

Something like:

- Added N / updated M places (names…)  
- Some still need_review  
- Live: https://nelsontraintest.github.io/TravelApp/web/  
- Wait 1–2 minutes, then reload Safari  

## After ingest on iPhone

1. Wait ~1–2 minutes for Pages  
2. Open/reload https://nelsontraintest.github.io/TravelApp/web/  
3. Use location or a Preview area  

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No reply on WhatsApp | `hermes gateway status` — start if stopped; confirm pair with `hermes whatsapp` |
| Gateway up but silent | Confirm Ollama/Gemma4 is running; check `hermes logs` |
| Ingest OK, site unchanged | Wait for Pages; hard-refresh Safari; confirm `git push` succeeded |
| Push failed | Fix git auth on the Mac (`gh auth status` / HTTPS credentials), re-run publish |
| Empty transcript | Captions disabled on the video — Hermes should stop without inventing places |
| Skill not used | New Hermes session after symlink; message should mention travel_app / ingest / YouTube |

## Related commands

```bash
# Publish only (after a manual merge)
cd /Users/nlee/DevelopmentProjects/projects/travel_app
./scripts/publish_places.sh "Add places from <title>"

# Local preview without publishing
./scripts/serve.sh
```
