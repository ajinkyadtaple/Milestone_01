"""Phase 5 Streamlit UI — light Zomato theme (Screens mockup)."""
from __future__ import annotations

import html
from typing import Any

import streamlit as st

from .config import BUDGET_LABELS, CUISINE_OPTIONS, LOCATIONS, MIN_RATINGS, groq_configured


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        :root {
            --zomato-red: #e23744;
            --bg-page: #f4f4f5;
            --text-primary: #1c1c1c;
            --text-muted: #6b7280;
        }

        .stApp {
            background: var(--bg-page);
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e5e7eb;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p {
            color: var(--text-primary) !important;
        }

        .block-container {
            padding-top: 1.5rem;
            max-width: 1200px;
        }

        .zomato-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.75rem;
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 0.85rem 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }

        .zomato-brand {
            display: flex;
            align-items: center;
            gap: 0.65rem;
        }

        .zomato-logo {
            width: 36px;
            height: 36px;
            background: var(--zomato-red);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
        }

        .zomato-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text-primary);
            margin: 0;
        }

        .zomato-badge {
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            background: #f3f4f6;
            color: var(--text-muted);
        }

        .zomato-api-active {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }

        .zomato-api-active .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
        }

        .zomato-api-offline .dot {
            background: #ef4444;
        }

        .hero-empty {
            background: #fff;
            border: 2px dashed #d1d5db;
            border-radius: 16px;
            padding: 2.5rem 1.5rem;
            text-align: center;
            margin-bottom: 1.25rem;
        }

        .hero-icon {
            width: 56px;
            height: 56px;
            margin: 0 auto 0.75rem;
            background: #fde8ea;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }

        .hero-empty h3 {
            color: var(--text-primary) !important;
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
        }

        .hero-empty p {
            color: var(--text-muted) !important;
            max-width: 520px;
            margin: 0 auto;
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .rec-card {
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        }

        .rec-rank {
            display: inline-block;
            font-size: 0.65rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            color: #fff;
            background: var(--zomato-red);
            padding: 0.25rem 0.55rem;
            border-radius: 6px;
            margin-bottom: 0.45rem;
        }

        .insight-box {
            background: #fef2f2;
            border-left: 3px solid var(--zomato-red);
            padding: 0.65rem 0.85rem;
            border-radius: 0 8px 8px 0;
            margin-top: 0.5rem;
            font-size: 0.9rem;
            color: #374151;
        }

        div[data-testid="stMetric"] {
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 0.65rem 0.85rem;
        }

        div[data-testid="stMetricValue"] {
            color: var(--zomato-red) !important;
        }

        .sidebar-subtitle {
            color: var(--text-muted) !important;
            font-size: 0.8rem;
            margin-top: -0.35rem;
            margin-bottom: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(session_id: str | None) -> None:
    api_class = "zomato-api-active" if groq_configured() else "zomato-api-offline zomato-api-active"
    api_label = "API Active" if groq_configured() else "API Offline"
    sid = session_id or "New"
    display_sid = sid[:12] + "…" if len(sid) > 12 else sid

    st.markdown(
        f"""
        <div class="zomato-header">
          <div class="zomato-brand">
            <div class="zomato-logo">🍴</div>
            <h1 class="zomato-title">Zomato AI</h1>
            <span class="zomato-badge">Beta</span>
            <span class="{api_class}"><span class="dot"></span> {api_label}</span>
          </div>
          <div style="font-size:0.875rem;color:#6b7280;">
            Session ID: <strong style="color:#1c1c1c;">{display_sid}</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(total: int, indexed: int, session_id: str | None) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Restaurants", f"{total:,}")
    with c2:
        st.metric("Vector index", f"{indexed:,}")
    with c3:
        st.metric("Session", (session_id or "New")[:8] or "—")


def render_welcome() -> None:
    st.markdown(
        """
        <div class="hero-empty">
          <div class="hero-icon">🍽️</div>
          <h3>Discover your next meal</h3>
          <p>
            Adjust the filters in the sidebar to allow our neural network to cross-reference
            thousands of reviews, menus, and real-time vibe data for your perfect match.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[dict[str, Any], bool, bool, str | None]:
    """Returns filters, search_clicked, new_session_clicked, follow_up text."""
    st.markdown(
        '<p class="sidebar-subtitle">Curated by Intelligence</p>',
        unsafe_allow_html=True,
    )

    location = st.selectbox("Location", LOCATIONS, format_func=lambda x: x or "Any area")
    cuisine = st.selectbox("Cuisine preference", CUISINE_OPTIONS, format_func=lambda x: x or "Any")
    budget_tier = st.selectbox(
        "Budget tier",
        options=["", "low", "medium", "high"],
        format_func=lambda x: BUDGET_LABELS[x],
    )

    col_a, col_b = st.columns(2)
    with col_a:
        max_cost = st.number_input(
            "Max cost (₹)",
            min_value=0,
            max_value=10000,
            value=2000,
            step=50,
            help="0 = no limit",
        )
    with col_b:
        min_rating = st.selectbox("Min rating", MIN_RATINGS, index=2, format_func=lambda x: f"{x:.1f}+" if x else "Any")

    description = st.text_area(
        "Contextual preferences",
        placeholder="Quiet rooftop for a date…",
        height=88,
    )

    search = st.button("✨ Get AI recommendations", type="primary", use_container_width=True)
    new_session = st.button("↻ New session", use_container_width=True)

    st.divider()
    st.subheader("Follow-up chat")
    for msg in st.session_state.get("chat", [])[-6:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    follow_up = st.chat_input("Refine your picks…")

    filters = {
        "location": location,
        "cuisine": cuisine,
        "budget_tier": budget_tier,
        "min_rating": float(min_rating),
        "max_cost": int(max_cost) if max_cost > 0 else None,
        "description": description,
    }
    return filters, search, new_session, follow_up


def render_results(result: Any) -> None:
    if result.message:
        st.success(result.message)
    if result.tools_used:
        st.caption(f"Tools: {' → '.join(result.tools_used)}")

    if not result.recommendations:
        st.warning("No restaurants matched your criteria. Try relaxing filters.")
        return

    st.subheader(f"Top {len(result.recommendations)} picks")
    for i, rec in enumerate(result.recommendations, 1):
        name = html.escape(rec.name)
        location = html.escape(rec.location)
        cuisines = html.escape(rec.cuisines)
        explanation = html.escape(rec.explanation)
        st.markdown(
            f"""
            <div class="rec-card">
              <span class="rec-rank">AI RECOMMENDATION #{i}</span>
              <h3 style="margin:0.25rem 0;color:#1c1c1c;">{name}</h3>
              <p style="color:#6b7280;margin:0.15rem 0;">
                📍 {location} · 🍴 {cuisines} · ★ {rec.rating:.1f} · ₹{rec.cost} for two
              </p>
              <div class="insight-box"><strong>AI insight:</strong> {explanation}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
