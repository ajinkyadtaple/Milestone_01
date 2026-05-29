"""Phase 5 configuration — env vars, filters, and paths."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PHASE5_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PHASE5_ROOT.parent
PHASE3_ROOT = REPO_ROOT / "Phase3"

LOCATIONS = [
    "",
    "Banashankari",
    "Basavanagudi",
    "Bellandur",
    "BTM",
    "Indiranagar",
    "Jayanagar",
    "JP Nagar",
    "Koramangala",
    "Malleshwaram",
    "Marathahalli",
    "Whitefield",
    "HSR",
]

CUISINE_OPTIONS = ["", "Asian", "Continental", "North Indian", "Italian", "Chinese", "South Indian"]

BUDGET_LABELS = {"": "Any", "low": "$ Low", "medium": "$$ Mid", "high": "$$$ High"}

MIN_RATINGS = [0.0, 3.5, 4.0, 4.5]

SECRET_KEYS = ("GROQ_API_KEY", "GROQ_MODEL", "GROQ_API_BASE_URL")


def ensure_phase3_path() -> None:
    phase3 = str(PHASE3_ROOT)
    if phase3 not in sys.path:
        sys.path.insert(0, phase3)


def configure_environment() -> None:
    """Load Phase3/.env locally and Streamlit Cloud secrets when available."""
    try:
        from dotenv import load_dotenv

        load_dotenv(PHASE3_ROOT / ".env")
        load_dotenv(REPO_ROOT / ".env")
        load_dotenv(PHASE5_ROOT / ".env")
    except ImportError:
        pass

    try:
        import streamlit as st

        for key in SECRET_KEYS:
            if key in st.secrets:
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass


def groq_configured() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))
