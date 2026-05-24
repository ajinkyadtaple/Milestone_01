from __future__ import annotations

import pandas as pd

from src.config import HYBRID_TOP_K, SEMANTIC_TOP_K
from src.filter import filter_restaurants
from src.vector_store import RestaurantVectorStore


def hybrid_search(
    df: pd.DataFrame,
    vector_store: RestaurantVectorStore,
    location: str = "",
    cuisine: str = "",
    budget_tier: str = "",
    min_rating: float = 0.0,
    max_cost: int | None = None,
    query: str = "",
    top_k: int = HYBRID_TOP_K,
) -> pd.DataFrame:
    filtered = filter_restaurants(
        df=df,
        location=location,
        cuisine=cuisine,
        budget_tier=budget_tier,
        min_rating=min_rating,
        max_cost=max_cost,
        limit=None,
    )
    if filtered.empty:
        return filtered

    query = (query or "").strip()
    if not query:
        return filtered.head(top_k)

    allowed_ids = filtered["restaurant_id"].astype(str).tolist()
    matches = vector_store.query_similar(
        query_text=query,
        restaurant_ids=allowed_ids,
        n_results=min(SEMANTIC_TOP_K, top_k, len(allowed_ids)),
    )
    if not matches:
        return filtered.head(top_k)

    rank_order = [m["restaurant_id"] for m in matches]
    ranked = filtered.set_index("restaurant_id").loc[rank_order].reset_index()
    ranked["semantic_score"] = [1 - (m["distance"] or 0) for m in matches]
    return ranked.head(top_k)
