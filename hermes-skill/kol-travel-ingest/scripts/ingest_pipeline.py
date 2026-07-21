#!/usr/bin/env python3
"""Single-command ingest pipeline: enrich → merge → validate → publish.

Usage:
    python3 ingest_pipeline.py /tmp/travel_app/extract_<id>.json [--publish]

Replaces the multi-step manual process so Gemma4/Hermes can call one command.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[2]
ENRICH = SCRIPT_DIR / "enrich_places.py"
MERGE = SCRIPT_DIR / "merge_places.py"
VALIDATE = SCRIPT_DIR / "validate_places.py"
PUBLISH = REPO / "scripts" / "publish_places.sh"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"  → {' '.join(str(c) for c in cmd)}", file=sys.stderr)
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description="Ingest pipeline: enrich → merge → validate → publish")
    parser.add_argument("extract", help="Path to extract JSON from Gemma4/Cursor")
    parser.add_argument("--publish", action="store_true", help="Run publish_places.sh after merge")
    parser.add_argument("--commit-msg", default="", help="Commit message for publish")
    args = parser.parse_args()

    extract_path = Path(args.extract)
    if not extract_path.exists():
        print(f"Error: {extract_path} not found", file=sys.stderr)
        sys.exit(1)

    # Step 1: Enrich
    print("\n[1/4] Enriching places with OSM data...", file=sys.stderr)
    result = run([sys.executable, str(ENRICH), str(extract_path)])
    if result.returncode != 0:
        print(f"Enrich failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Write enriched output to temp file
    enriched_path = extract_path.with_suffix(".enriched.json")
    enriched_path.write_text(result.stdout, encoding="utf-8")
    print(f"  Enriched → {enriched_path}", file=sys.stderr)

    # Step 2: Merge
    print("\n[2/4] Merging into places.json...", file=sys.stderr)
    result = run([sys.executable, str(MERGE), str(enriched_path)])
    if result.returncode != 0:
        print(f"Merge failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout, file=sys.stderr)

    # Step 3: Validate
    print("\n[3/4] Validating places.json...", file=sys.stderr)
    result = run([sys.executable, str(VALIDATE)])
    if result.returncode != 0:
        print(f"Validation failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout)

    # Step 4: Publish (optional)
    if args.publish:
        print("\n[4/4] Publishing to GitHub Pages...", file=sys.stderr)
        msg = args.commit_msg or f"Add places from ingest ({extract_path.stem})"
        result = run(["bash", str(PUBLISH), msg])
        if result.returncode != 0:
            print(f"Publish failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)
        print(result.stdout)
    else:
        print("\n[4/4] Skipping publish (use --publish to push).", file=sys.stderr)

    print("\nPipeline complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
