import pandas as pd
from src.config import BUDGET_LOW_MAX, BUDGET_MEDIUM_MAX


def filter_restaurants(
    df: pd.DataFrame,
    location: str = "",
    cuisine: str = "",
    budget_tier: str = "",
    min_rating: float = 0.0,
    max_cost: int | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    filtered = df.copy()

    if location:
        loc_clean = location.strip().lower()
        filtered = filtered[filtered["location_clean"].str.contains(loc_clean, na=False)]

    if cuisine:
        cui_clean = cuisine.strip().lower()
        filtered = filtered[filtered["cuisines_clean"].str.contains(cui_clean, na=False)]

    if min_rating > 0.0:
        filtered = filtered[filtered["rate_float"] >= min_rating]

    if max_cost is not None and max_cost > 0:
        filtered = filtered[filtered["cost_clean"] <= int(max_cost)]

    if budget_tier:
        b_tier = budget_tier.strip().lower()
        if b_tier == "low":
            filtered = filtered[filtered["cost_clean"] <= BUDGET_LOW_MAX]
        elif b_tier == "medium":
            filtered = filtered[
                (filtered["cost_clean"] > BUDGET_LOW_MAX)
                & (filtered["cost_clean"] <= BUDGET_MEDIUM_MAX)
            ]
        elif b_tier == "high":
            filtered = filtered[filtered["cost_clean"] > BUDGET_MEDIUM_MAX]

    filtered = filtered.sort_values(by=["rate_float", "votes"], ascending=[False, False])
    if limit is not None:
        return filtered.head(limit)
    return filtered
