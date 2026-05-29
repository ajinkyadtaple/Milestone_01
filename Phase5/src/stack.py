"""Load Phase 3 agent stack in-process for Streamlit."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import pandas as pd
import streamlit as st

from .config import ensure_phase3_path


@st.cache_resource(show_spinner="Loading restaurant data and search engine…")
def load_stack():
    ensure_phase3_path()

    from src.agent import RecommendationAgent
    from src.config import ENRICHED_DATA_PATH, MAX_SESSION_TURNS
    from src.session_memory import SessionMemory
    from src.vector_store import NullVectorStore, RestaurantVectorStore

    if not ENRICHED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing {ENRICHED_DATA_PATH}. Run: cd Phase2 && python -m src.ingestion"
        )

    df = pd.read_csv(ENRICHED_DATA_PATH)
    if "restaurant_id" not in df.columns:
        df["restaurant_id"] = df.index.astype(str)

    vector_store = NullVectorStore()
    indexed = 0
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            vs = pool.submit(RestaurantVectorStore).result(timeout=20)
        indexed = vs.count()
        vector_store = vs
    except (FuturesTimeout, Exception):
        pass

    memory = SessionMemory(max_turns=MAX_SESSION_TURNS)
    agent = RecommendationAgent(df, vector_store, memory)
    return agent, indexed, len(df)
