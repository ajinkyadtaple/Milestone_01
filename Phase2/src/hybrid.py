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
    query: str = "",
    top_k: int = HYBRID_TOP_K,
) -> pd.DataFrame:
    """
    Hybrid retrieval:
    1. Strict pandas filters for hard constraints.
    2. Semantic ranking on the filtered subset for natural-language query.
    3. If no query, return top rows by rating/votes from the filtered set.
    """
    filtered = filter_restaurants(
        df=df,
        location=location,
        cuisine=cuisine,
        budget_tier=budget_tier,
        min_rating=min_rating,
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


def format_candidates_preview(df: pd.DataFrame, max_rows: int = 5) -> str:
    lines = []
    for _, row in df.head(max_rows).iterrows():
        score = f", semantic={row['semantic_score']:.3f}" if "semantic_score" in row else ""
        lines.append(
            f"- {row['name']} ({row['location']}) | {row['rate_float']}★ | ₹{row['cost_clean']}{score}"
        )
    return "\n".join(lines)
