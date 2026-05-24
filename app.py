"""
Vercel ASGI entrypoint — exposes the Phase 3 FastAPI API at the repo root.

Vercel looks for a top-level ``app`` in app.py, index.py, server.py, or main.py.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHASE3 = ROOT / "Phase3"

if str(PHASE3) not in sys.path:
    sys.path.insert(0, str(PHASE3))

try:
    from dotenv import load_dotenv

    load_dotenv(PHASE3 / ".env")
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from fastapi.responses import JSONResponse
from src.main import app  # noqa: E402


@app.get("/runtime-config.json", include_in_schema=False)
async def runtime_config():
    """Same-origin API for Phase 4 static UI served from ``public/``."""
    return JSONResponse(
        {
            "apiBase": os.getenv("PHASE3_API_BASE", "").rstrip("/"),
            "uiBase": os.getenv("VERCEL_URL", "").rstrip("/"),
        }
    )
