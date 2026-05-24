from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.config import HYBRID_TOP_K
from src.filter import filter_restaurants
from src.hybrid import hybrid_search
from src.vector_store import RestaurantVectorStore


@dataclass
class ToolResult:
    tool_name: str
    candidates: pd.DataFrame
    filters_applied: dict[str, Any]
    note: str = ""


class SearchTools:
    """Custom search tools invoked by the ReAct agent."""

    def __init__(self, df: pd.DataFrame, vector_store: RestaurantVectorStore):
        self.df = df
        self.vector_store = vector_store

    def structured_search(
        self,
        location: str = "",
        cuisine: str = "",
        budget_tier: str = "",
        min_rating: float = 0.0,
        max_cost: int | None = None,
        limit: int = HYBRID_TOP_K,
    ) -> ToolResult:
        filters = {
            "location": location,
            "cuisine": cuisine,
            "budget_tier": budget_tier,
            "min_rating": min_rating,
            "max_cost": max_cost,
        }
        candidates = filter_restaurants(
            self.df,
            location=location,
            cuisine=cuisine,
            budget_tier=budget_tier,
            min_rating=min_rating,
            max_cost=max_cost,
            limit=limit,
        )
        return ToolResult(
            tool_name="structured_search",
            candidates=candidates,
            filters_applied=filters,
            note=f"Structured filter returned {len(candidates)} rows.",
        )

    def hybrid_search(
        self,
        query: str,
        location: str = "",
        cuisine: str = "",
        budget_tier: str = "",
        min_rating: float = 0.0,
        max_cost: int | None = None,
    ) -> ToolResult:
        filters = {
            "location": location,
            "cuisine": cuisine,
            "budget_tier": budget_tier,
            "min_rating": min_rating,
            "max_cost": max_cost,
            "query": query,
        }
        candidates = hybrid_search(
            df=self.df,
            vector_store=self.vector_store,
            location=location,
            cuisine=cuisine,
            budget_tier=budget_tier,
            min_rating=min_rating,
            max_cost=max_cost,
            query=query,
        )
        return ToolResult(
            tool_name="hybrid_search",
            candidates=candidates,
            filters_applied=filters,
            note=f"Hybrid search returned {len(candidates)} rows.",
        )

    def refine_previous(
        self,
        restaurant_name: str,
        refinement_query: str,
        base_filters: dict[str, Any],
    ) -> ToolResult:
        """Narrow to a prior recommendation and re-rank with a follow-up preference."""
        subset = self.df[self.df["name"].str.lower() == restaurant_name.strip().lower()]
        if subset.empty:
            subset = self.df[
                self.df["name"].str.contains(restaurant_name.strip(), case=False, na=False)
            ]

        filters = {**base_filters, "focus_restaurant": restaurant_name, "query": refinement_query}
        if subset.empty:
            return ToolResult(
                tool_name="refine_previous",
                candidates=pd.DataFrame(),
                filters_applied=filters,
                note=f"Could not find prior restaurant '{restaurant_name}'.",
            )

        if refinement_query.strip() and self.vector_store.count() > 0:
            ids = subset["restaurant_id"].astype(str).tolist()
            matches = self.vector_store.query_similar(refinement_query, ids, n_results=min(5, len(ids)))
            if matches:
                order = [m["restaurant_id"] for m in matches]
                candidates = subset.set_index("restaurant_id").loc[order].reset_index()
            else:
                candidates = subset.head(HYBRID_TOP_K)
        else:
            candidates = subset.head(HYBRID_TOP_K)

        return ToolResult(
            tool_name="refine_previous",
            candidates=candidates,
            filters_applied=filters,
            note=f"Refined selection around '{restaurant_name}'.",
        )

    def relax_filters(
        self,
        location: str = "",
        cuisine: str = "",
        budget_tier: str = "",
        min_rating: float = 0.0,
        query: str = "",
    ) -> ToolResult:
        """Progressively relax constraints when strict filters return nothing."""
        attempts = [
            (min_rating, cuisine, budget_tier, location),
            (max(0.0, min_rating - 0.5), cuisine, budget_tier, location),
            (max(0.0, min_rating - 0.5), cuisine, "", location),
            (0.0, cuisine, "", location),
            (0.0, "", "", location),
        ]
        seen: set[tuple] = set()
        for rating, cui, budget, loc in attempts:
            key = (rating, cui, budget, loc)
            if key in seen:
                continue
            seen.add(key)
            if query.strip():
                result = self.hybrid_search(query, loc, cui, budget, rating)
            else:
                result = self.structured_search(loc, cui, budget, rating)
            if not result.candidates.empty:
                result.tool_name = "relax_filters"
                result.note = "Relaxed filters to find matches."
                result.filters_applied["relaxed"] = True
                return result

        return ToolResult(
            tool_name="relax_filters",
            candidates=pd.DataFrame(),
            filters_applied={
                "location": location,
                "cuisine": cuisine,
                "budget_tier": budget_tier,
                "min_rating": min_rating,
                "query": query,
            },
            note="No matches even after relaxing filters.",
        )
