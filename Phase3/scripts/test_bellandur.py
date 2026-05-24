"""Live test: Bellandur, max cost 2000, min rating 4.0 → top 5 via Groq."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.agent import RecommendationAgent
from src.config import ENRICHED_DATA_PATH
from src.groq_client import is_groq_configured
from src.session_memory import SessionMemory
from src.vector_store import RestaurantVectorStore


def main():
    if not is_groq_configured():
        print("ERROR: Set GROQ_API_KEY in Phase3/.env before running this test.")
        sys.exit(1)

    print("Loading dataset...")
    df = pd.read_csv(ENRICHED_DATA_PATH)
    if "restaurant_id" not in df.columns:
        df["restaurant_id"] = df.index.astype(str)

    store = RestaurantVectorStore()
    agent = RecommendationAgent(df, store, SessionMemory())

    print("\n=== Live test ===")
    print("Location: Bellandur | Max budget (for two): ₹2000 | Min rating: 4.0\n")

    result = agent.run(
        session_id=None,
        message="Top restaurants in Bellandur within budget, highly rated",
        location="Bellandur",
        min_rating=4.0,
        max_cost=2000,
    )

    print(f"Session: {result.session_id}")
    print(f"Tools: {', '.join(result.tools_used)}")
    print(f"Message: {result.message}\n")
    print(f"Top {len(result.recommendations)} recommendations (Groq):\n")

    for i, rec in enumerate(result.recommendations, 1):
        print(f"{i}. {rec.name}")
        print(f"   Rating: {rec.rating} | Cost for two: ₹{rec.cost}")
        print(f"   {rec.cuisines} @ {rec.location}")
        print(f"   {rec.explanation}\n")

    if not result.recommendations:
        print("No recommendations returned. Check filters or Groq API.")
        sys.exit(1)


if __name__ == "__main__":
    main()
