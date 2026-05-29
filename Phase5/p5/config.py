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
    """Put Phase3 first on sys.path; drop cached ``src`` if it is not Phase3's package."""
    phase3 = str(PHASE3_ROOT)
    src_mod = sys.modules.get("src")
    if src_mod is not None:
        mod_file = (getattr(src_mod, "__file__", None) or "").replace("\\", "/")
        if "/Phase3/" not in mod_file:
            for key in list(sys.modules):
                if key == "src" or key.startswith("src."):
                    del sys.modules[key]
    if phase3 in sys.path:
        sys.path.remove(phase3)
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
