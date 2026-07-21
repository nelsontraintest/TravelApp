#!/usr/bin/env bash
# Serve Scouted so /web and /data are available (needed for places.json + geolocation on LAN).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8765}"
cd "$ROOT"
echo "Scouted → http://127.0.0.1:${PORT}/web/"
echo "On iPhone (same Wi‑Fi): http://$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "<your-mac-ip>"):${PORT}/web/"
echo "Ctrl+C to stop."
exec python3 -m http.server "$PORT" --bind 0.0.0.0
