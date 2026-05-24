from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.config import MAX_AGENT_STEPS
from src.groq_client import chat_json, is_groq_configured
from src.llm_client import RecommendationItem, RecommendationResponse, get_recommendations
from src.session_memory import SessionMemory, SessionState
from src.tools import SearchTools, ToolResult
from src.vector_store import RestaurantVectorStore


@dataclass
class AgentResult:
    session_id: str
    recommendations: list[RecommendationItem]
    message: str
    filters_applied: dict[str, Any]
    tools_used: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)


ORDINAL_MAP = {
    "first": 0,
    "1st": 0,
    "one": 0,
    "second": 1,
    "2nd": 1,
    "two": 1,
    "third": 2,
    "3rd": 2,
    "three": 2,
}


def _empty_filters() -> dict[str, Any]:
    return {
        "location": "",
        "cuisine": "",
        "budget_tier": "",
        "min_rating": 0.0,
        "max_cost": None,
        "query": "",
    }


def _parse_max_cost(filters: dict[str, Any]) -> int | None:
    val = filters.get("max_cost")
    if val is None or val == "":
        return None
    try:
        n = int(val)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def merge_filters(
    session: SessionState,
    explicit: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    """Merge explicit API fields with session state; handle replacement cues in message."""
    merged = {**_empty_filters(), **session.active_filters}
    for key in ("location", "cuisine", "budget_tier"):
        val = explicit.get(key)
        if val is not None and str(val).strip():
            merged[key] = str(val).strip()
    if explicit.get("min_rating"):
        merged["min_rating"] = float(explicit["min_rating"])
    if explicit.get("max_cost") is not None:
        merged["max_cost"] = int(explicit["max_cost"])
    if explicit.get("description") or explicit.get("query"):
        merged["query"] = (explicit.get("description") or explicit.get("query") or "").strip()

    msg = (message or "").strip()
    if not msg:
        return merged

    lower = msg.lower()
    replace_cues = ("instead", "actually", "switch to", "change to", "make it", "rather than")
    if any(cue in lower for cue in replace_cues):
        cuisine_match = re.search(
            r"(?:instead|actually|switch to|change to|make it)\s+(?:\w+\s+){0,2}?([a-z\s]+?)(?:\s+cuisine|\s+food|\s+places?|$)",
            lower,
        )
        if cuisine_match:
            merged["cuisine"] = cuisine_match.group(1).strip()

        loc_match = re.search(r"(?:in|near|around)\s+([a-z0-9\s]+?)(?:\s+with|\s+that|$)", lower)
        if loc_match and "instead" in lower:
            merged["location"] = loc_match.group(1).strip()

    if not merged["query"]:
        merged["query"] = msg
    elif msg not in merged["query"]:
        merged["query"] = f"{merged['query']}. {msg}"

    return merged


def detect_follow_up_target(message: str, session: SessionState) -> str | None:
    if not session.last_recommendations:
        return None
    lower = message.lower()
    for word, idx in ORDINAL_MAP.items():
        if re.search(rf"\b{word}\b", lower) and idx < len(session.last_recommendations):
            return session.last_recommendations[idx]["name"]
    return None


def rule_based_tool_choice(message: str, filters: dict[str, Any], session: SessionState) -> str:
    if detect_follow_up_target(message, session):
        return "refine_previous"
    if filters.get("query", "").strip():
        return "hybrid_search"
    if any(filters.get(k) for k in ("location", "cuisine", "budget_tier")) or filters.get("min_rating", 0) > 0:
        return "structured_search"
    if session.last_recommendations:
        return "refine_previous"
    return "structured_search"


def llm_choose_tool(
    message: str,
    filters: dict[str, Any],
    session: SessionState,
) -> str | None:
    if not is_groq_configured():
        return None

    tools_doc = """
    Available tools:
    - structured_search: hard filters only (location, cuisine, budget, min_rating)
    - hybrid_search: hard filters + semantic match on natural language query
    - refine_previous: user refers to a prior recommendation (e.g. "the first one with outdoor seating")
    - relax_filters: strict filters returned zero rows; loosen constraints
    Return JSON: {"tool": "<name>", "reason": "<short>"}
    """
    prompt = f"""
    {tools_doc}

    Conversation history:
    {session.history_summary()}

    Active filters: {json.dumps(filters)}
    User message: {message}
    Last recommendations: {[r.get('name') for r in session.last_recommendations[:3]]}
    """

    try:
        data = chat_json(
            "You are a restaurant search planner. Reply with JSON only.",
            prompt.strip(),
            temperature=0.0,
        )
        tool = data.get("tool", "")
        if tool in ("structured_search", "hybrid_search", "refine_previous", "relax_filters"):
            return tool
    except Exception as e:
        print(f"Agent planner fallback: {e}")
    return None


class RecommendationAgent:
    """ReAct-style orchestrator: plan → tool → observe → format."""

    def __init__(
        self,
        df: pd.DataFrame,
        vector_store: RestaurantVectorStore,
        memory: SessionMemory,
    ):
        self.df = df
        self.vector_store = vector_store
        self.memory = memory
        self.tools = SearchTools(df, vector_store)

    def run(
        self,
        session_id: str | None,
        message: str,
        location: str = "",
        cuisine: str = "",
        budget_tier: str = "",
        min_rating: float = 0.0,
        max_cost: int | None = None,
        description: str = "",
    ) -> AgentResult:
        sid, session = self.memory.get_or_create(session_id)
        user_text = (description or message or "").strip()
        explicit = {
            "location": location,
            "cuisine": cuisine,
            "budget_tier": budget_tier,
            "min_rating": min_rating,
            "max_cost": max_cost,
            "description": user_text,
        }
        filters = merge_filters(session, explicit, user_text)
        tools_used: list[str] = []
        steps: list[str] = []

        index_ok = self.vector_store.count() > 0
        tool_name = llm_choose_tool(user_text, filters, session) or rule_based_tool_choice(
            user_text, filters, session
        )
        if tool_name == "hybrid_search" and not index_ok:
            tool_name = "structured_search"
            steps.append("Plan: vector index empty — using structured_search")
        steps.append(f"Plan: use {tool_name}")

        result: ToolResult | None = None
        for step in range(MAX_AGENT_STEPS):
            max_c = _parse_max_cost(filters)
            if tool_name == "structured_search":
                result = self.tools.structured_search(
                    filters["location"],
                    filters["cuisine"],
                    filters["budget_tier"],
                    float(filters.get("min_rating") or 0),
                    max_c,
                )
            elif tool_name == "hybrid_search":
                result = self.tools.hybrid_search(
                    filters.get("query", ""),
                    filters["location"],
                    filters["cuisine"],
                    filters["budget_tier"],
                    float(filters.get("min_rating") or 0),
                    max_c,
                )
            elif tool_name == "refine_previous":
                target = detect_follow_up_target(user_text, session)
                if not target and session.last_recommendations:
                    target = session.last_recommendations[0]["name"]
                result = self.tools.refine_previous(
                    target or "",
                    filters.get("query", user_text),
                    filters,
                )
            elif tool_name == "relax_filters":
                result = self.tools.relax_filters(
                    filters["location"],
                    filters["cuisine"],
                    filters["budget_tier"],
                    float(filters.get("min_rating") or 0),
                    filters.get("query", ""),
                )
            else:
                break

            tools_used.append(result.tool_name)
            steps.append(f"Act: {result.tool_name} → {result.note}")

            if not result.candidates.empty:
                break
            if result.tool_name == "relax_filters":
                break
            tool_name = "relax_filters"
            steps.append("Observe: empty results, relaxing filters")

        if result is None or result.candidates.empty:
            session.add_turn("user", user_text, filters, tools_used, self.memory.max_turns)
            session.active_filters = result.filters_applied if result else filters
            return AgentResult(
                session_id=sid,
                recommendations=[],
                message=result.note if result else "No matching restaurants found.",
                filters_applied=filters,
                tools_used=tools_used,
                steps=steps,
            )

        llm_response: RecommendationResponse = get_recommendations(
            result.candidates,
            user_description=filters.get("query", user_text),
        )

        session.active_filters = result.filters_applied
        session.last_candidate_ids = result.candidates["restaurant_id"].astype(str).tolist()
        session.last_recommendations = [r.model_dump() for r in llm_response.recommendations]
        session.add_turn("user", user_text, result.filters_applied, tools_used, self.memory.max_turns)
        session.add_turn(
            "assistant",
            f"Returned {len(llm_response.recommendations)} recommendations.",
            result.filters_applied,
            ["format_recommendations"],
            self.memory.max_turns,
        )
        tools_used.append("format_recommendations")
        steps.append("Act: format_recommendations → ranked top picks")

        summary = (
            f"Found {len(result.candidates)} candidates via {', '.join(tools_used[:-1])}; "
            f"returned {len(llm_response.recommendations)} recommendations."
        )
        return AgentResult(
            session_id=sid,
            recommendations=llm_response.recommendations,
            message=summary,
            filters_applied=result.filters_applied,
            tools_used=tools_used,
            steps=steps,
        )
