"""
Zomato AI — Streamlit UI for restaurant recommendations.
Uses Phase 3 agent (Groq + hybrid search). Run from repo root:

    pip install -r Phase3/requirements.txt streamlit
    streamlit run streamlit_app.py
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
PHASE3 = ROOT / "Phase3"


def configure_environment() -> None:
    """Load .env locally and Streamlit Cloud secrets in production."""
    try:
        from dotenv import load_dotenv

        load_dotenv(PHASE3 / ".env")
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    try:
        secrets = st.secrets
        for key in ("GROQ_API_KEY", "GROQ_MODEL", "GROQ_API_BASE_URL"):
            if key in secrets:
                os.environ[key] = str(secrets[key])
    except Exception:
        pass


configure_environment()

if str(PHASE3) not in sys.path:
    sys.path.insert(0, str(PHASE3))

import pandas as pd

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

BUDGET_LABELS = {"": "Any", "low": "$ Low", "medium": "$$ Mid", "high": "$$$ High"}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(145deg, #0b0c10 0%, #151b26 50%, #1a1020 100%); }
        h1, h2, h3, label, p { color: #f5f5f7 !important; }
        .zomato-title span { color: #e23744; }
        div[data-testid="stMetricValue"] { color: #e23744; }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner="Loading restaurant data and search engine…")
def load_stack():
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


def init_session() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "chat" not in st.session_state:
        st.session_state.chat = []


def main() -> None:
    st.set_page_config(
        page_title="Zomato AI",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    init_session()

    st.markdown('<h1 class="zomato-title">Zomato<span>AI</span></h1>', unsafe_allow_html=True)
    st.caption("Streamlit UI · Phase 3 agent · Groq recommendations")

    try:
        agent, indexed, total = load_stack()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"Failed to load app: {e}")
        st.stop()

    if not os.getenv("GROQ_API_KEY"):
        st.warning(
            "GROQ_API_KEY is not set. Add it to Phase3/.env locally or "
            "Streamlit Cloud **Settings → Secrets** (see `.streamlit/secrets.toml.example`)."
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Restaurants", f"{total:,}")
    with col2:
        st.metric("Vector index", indexed)
    with col3:
        st.metric("Session", (st.session_state.session_id or "New")[:8] or "—")

    with st.sidebar:
        st.header("Find restaurants")
        location = st.selectbox("Location", LOCATIONS, format_func=lambda x: x or "Any area")
        cuisine = st.text_input("Cuisine", placeholder="e.g. Italian, North Indian")
        budget_tier = st.selectbox(
            "Budget tier",
            options=["", "low", "medium", "high"],
            format_func=lambda x: BUDGET_LABELS[x],
        )
        max_cost = st.number_input(
            "Max cost for two (₹)",
            min_value=0,
            max_value=10000,
            value=0,
            step=50,
            help="0 = no limit",
        )
        min_rating = st.selectbox("Minimum rating", [0.0, 3.5, 4.0, 4.5], index=2)
        description = st.text_area(
            "Soft preferences",
            placeholder="Quiet rooftop, family-friendly, spicy food…",
            height=100,
        )

        search = st.button("Get AI recommendations", type="primary", use_container_width=True)
        if st.button("New session", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.chat = []
            st.rerun()

        st.divider()
        st.subheader("Follow-up chat")
        for msg in st.session_state.chat[-6:]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        follow_up = st.chat_input("Refine your picks…")

    if search:
        with st.spinner("Searching and ranking with AI…"):
            result = agent.run(
                session_id=st.session_state.session_id,
                message=description,
                location=location,
                cuisine=cuisine,
                budget_tier=budget_tier,
                min_rating=float(min_rating),
                max_cost=int(max_cost) if max_cost > 0 else None,
                description=description,
            )
        st.session_state.session_id = result.session_id
        st.session_state.last_result = result
        if description:
            st.session_state.chat.append({"role": "user", "content": description})
            summary = result.message or f"{len(result.recommendations)} recommendations"
            st.session_state.chat.append({"role": "assistant", "content": summary})

    elif follow_up:
        if not st.session_state.session_id:
            st.sidebar.warning("Run a search first to start a session.")
        else:
            with st.spinner("Processing follow-up…"):
                result = agent.run(
                    session_id=st.session_state.session_id,
                    message=follow_up,
                    description=follow_up,
                )
            st.session_state.session_id = result.session_id
            st.session_state.last_result = result
            st.session_state.chat.append({"role": "user", "content": follow_up})
            st.session_state.chat.append(
                {
                    "role": "assistant",
                    "content": result.message or f"{len(result.recommendations)} updated picks",
                }
            )
            st.rerun()

    result = st.session_state.get("last_result")
    if result is None:
        st.info("Set filters in the sidebar and click **Get AI recommendations**.")
        return

    if result.message:
        st.success(result.message)
    if result.tools_used:
        st.caption(f"Tools: {' → '.join(result.tools_used)}")

    if not result.recommendations:
        st.warning("No restaurants matched your criteria. Try relaxing filters.")
        return

    st.subheader(f"Top {len(result.recommendations)} picks")
    for i, rec in enumerate(result.recommendations, 1):
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"### {i}. {rec.name}")
                st.write(f"📍 {rec.location} · 🍴 {rec.cuisines}")
            with c2:
                st.markdown(f"**★ {rec.rating:.1f}**")
                st.write(f"₹{rec.cost} for two")
            st.markdown("**AI insight**")
            st.write(rec.explanation)


if __name__ == "__main__":
    main()
