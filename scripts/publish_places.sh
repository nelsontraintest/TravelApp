#!/usr/bin/env bash
# Validate places.json, commit only that file, push to origin/main for GitHub Pages.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIVE_URL="https://nelsontraintest.github.io/TravelApp/web/"
MSG="${1:-Add places from WhatsApp ingest}"

cd "$ROOT"

python3 "$ROOT/hermes-skill/kol-travel-ingest/scripts/validate_places.py"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $ROOT" >&2
  exit 1
fi

if git diff --quiet -- data/places.json && git diff --cached --quiet -- data/places.json; then
  # Also detect untracked (shouldn't happen) or no file change vs HEAD
  if git diff --quiet HEAD -- data/places.json 2>/dev/null; then
    echo "No changes in data/places.json — nothing to publish."
    echo "Live app: $LIVE_URL"
    exit 0
  fi
fi

git add -- data/places.json
git commit -m "$MSG"
git push origin main

echo "Published data/places.json to origin/main."
echo "GitHub Pages usually updates in 1–2 minutes."
echo "Live app: $LIVE_URL"
