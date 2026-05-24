"""Copy Phase 4 static assets into ``public/`` for Vercel CDN before deploy."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Phase4" / "public"
DEST = ROOT / "public"


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Phase 4 public folder not found: {SRC}")
    if DEST.exists():
        shutil.rmtree(DEST)
    shutil.copytree(SRC, DEST)
    print(f"Copied UI assets: {SRC} -> {DEST}", flush=True)


if __name__ == "__main__":
    main()
