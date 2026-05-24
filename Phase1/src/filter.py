import pandas as pd
from src.config import BUDGET_LOW_MAX, BUDGET_MEDIUM_MAX

def filter_restaurants(df: pd.DataFrame, 
                       location: str = "", 
                       cuisine: str = "", 
                       budget_tier: str = "", 
                       min_rating: float = 0.0, 
                       limit: int = 20) -> pd.DataFrame:
    """
    Filter the cleaned restaurant DataFrame based on strict user constraints.
    Returns the top matches sorted by rating and popularity (votes).
    """
    filtered = df.copy()

    # 1. Location filter (substring case-insensitive match)
    if location:
        loc_clean = location.strip().lower()
        filtered = filtered[filtered['location_clean'].str.contains(loc_clean, na=False)]

    # 2. Cuisine filter (substring case-insensitive match)
    if cuisine:
        cui_clean = cuisine.strip().lower()
        filtered = filtered[filtered['cuisines_clean'].str.contains(cui_clean, na=False)]

    # 3. Minimum rating filter
    if min_rating > 0.0:
        filtered = filtered[filtered['rate_float'] >= min_rating]

    # 4. Budget filter
    if budget_tier:
        b_tier = budget_tier.strip().lower()
        if b_tier == "low":
            filtered = filtered[filtered['cost_clean'] <= BUDGET_LOW_MAX]
        elif b_tier == "medium":
            filtered = filtered[(filtered['cost_clean'] > BUDGET_LOW_MAX) & (filtered['cost_clean'] <= BUDGET_MEDIUM_MAX)]
        elif b_tier == "high":
            filtered = filtered[filtered['cost_clean'] > BUDGET_MEDIUM_MAX]

    # Sort results by rate (descending) and popularity/votes (descending) to ensure quality
    filtered = filtered.sort_values(by=['rate_float', 'votes'], ascending=[False, False])

    # Return top N matches
    return filtered.head(limit)
