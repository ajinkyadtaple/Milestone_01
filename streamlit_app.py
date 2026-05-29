"""
Streamlit Cloud entrypoint — delegates to Phase 5.

Streamlit Community Cloud expects ``streamlit_app.py`` at the repo root.
Implementation lives in ``Phase5/streamlit_app.py``.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

PHASE5_APP = Path(__file__).resolve().parent / "Phase5" / "streamlit_app.py"

_spec = importlib.util.spec_from_file_location("phase5_streamlit", PHASE5_APP)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load Phase 5 app from {PHASE5_APP}")

_phase5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_phase5)

_phase5.main()
