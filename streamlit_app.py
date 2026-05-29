"""
Streamlit Cloud entrypoint — delegates to Phase 5.

Streamlit Community Cloud expects ``streamlit_app.py`` at the repo root.
Implementation lives in ``Phase5/streamlit_app.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHASE3 = ROOT / "Phase3"
PHASE5 = ROOT / "Phase5"

# Phase3 must be importable as ``src.*`` before Phase5 loads.
if str(PHASE3) not in sys.path:
    sys.path.insert(0, str(PHASE3))

PHASE5_APP = PHASE5 / "streamlit_app.py"

import importlib.util

_spec = importlib.util.spec_from_file_location("phase5_streamlit", PHASE5_APP)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load Phase 5 app from {PHASE5_APP}")

_phase5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_phase5)

_phase5.main()
