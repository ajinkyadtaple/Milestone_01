"""
Phase 5: Streamlit Cloud deployment — in-process Phase 3 agent.

Local:
    cd Phase5
    pip install -r requirements.txt
    streamlit run streamlit_app.py

Streamlit Cloud uses repo-root ``streamlit_app.py`` (thin wrapper).
"""
from __future__ import annotations

import sys
from pathlib import Path

PHASE5_ROOT = Path(__file__).resolve().parent
if str(PHASE5_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE5_ROOT))

import streamlit as st

from p5.config import configure_environment, groq_configured
from p5.stack import load_stack
from p5.ui import (
    inject_css,
    render_header,
    render_metrics,
    render_results,
    render_sidebar,
    render_welcome,
)

configure_environment()


def init_session() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "last_result" not in st.session_state:
        st.session_state.last_result = None


def run_agent(agent, *, session_id, message, filters):
    return agent.run(
        session_id=session_id,
        message=message,
        location=filters["location"],
        cuisine=filters["cuisine"],
        budget_tier=filters["budget_tier"],
        min_rating=filters["min_rating"],
        max_cost=filters["max_cost"],
        description=filters["description"] or message,
    )


def append_chat(user_text: str, assistant_text: str) -> None:
    st.session_state.chat.append({"role": "user", "content": user_text})
    st.session_state.chat.append({"role": "assistant", "content": assistant_text})


def main() -> None:
    st.set_page_config(
        page_title="Zomato AI",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    init_session()

    with st.sidebar:
        st.header("Find restaurants")

    render_header(st.session_state.session_id)

    try:
        agent, indexed, total = load_stack()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"Failed to load app: {e}")
        st.stop()

    if not groq_configured():
        st.warning(
            "GROQ_API_KEY is not set. Add it to `Phase3/.env` locally or "
            "Streamlit Cloud **Settings → Secrets** (see `.streamlit/secrets.toml.example`)."
        )

    render_metrics(total, indexed, st.session_state.session_id)

    with st.sidebar:
        filters, search, new_session, follow_up = render_sidebar()

    if new_session:
        st.session_state.session_id = None
        st.session_state.chat = []
        st.session_state.last_result = None
        st.rerun()

    if search:
        with st.spinner("Searching and ranking with AI…"):
            result = run_agent(
                agent,
                session_id=st.session_state.session_id,
                message=filters["description"],
                filters=filters,
            )
        st.session_state.session_id = result.session_id
        st.session_state.last_result = result
        if filters["description"]:
            append_chat(
                filters["description"],
                result.message or f"{len(result.recommendations)} recommendations",
            )

    elif follow_up:
        if not st.session_state.session_id:
            st.sidebar.warning("Run a search first to start a session.")
        else:
            with st.spinner("Processing follow-up…"):
                result = run_agent(
                    agent,
                    session_id=st.session_state.session_id,
                    message=follow_up,
                    filters={**filters, "description": follow_up},
                )
            st.session_state.session_id = result.session_id
            st.session_state.last_result = result
            append_chat(
                follow_up,
                result.message or f"{len(result.recommendations)} updated picks",
            )
            st.rerun()

    result = st.session_state.last_result
    if result is None:
        render_welcome()
        return

    render_results(result)


if __name__ == "__main__":
    main()
