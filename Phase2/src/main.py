"""
Phase 2 CLI: hybrid retrieval (pandas filters + Chroma semantic search) + LLM ranking.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

# Allow running as `python -m src.main` from Phase2 root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ENRICHED_DATA_PATH, INDEX_MAX_ROWS
from src.hybrid import format_candidates_preview, hybrid_search
from src.ingestion import run_ingestion
from src.llm_client import get_recommendations
from src.vector_store import RestaurantVectorStore


def load_dataset() -> pd.DataFrame:
    if not ENRICHED_DATA_PATH.exists():
        print("Enriched CSV not found. Running ingestion (downloads from Hugging Face)...")
        return run_ingestion()
    return pd.read_csv(ENRICHED_DATA_PATH)


def ensure_index(
    df: pd.DataFrame,
    store: RestaurantVectorStore,
    rebuild: bool = False,
    max_rows: int | None = None,
) -> None:
    work_df = df.head(max_rows) if max_rows else df
    if max_rows:
        print(f"Indexing subset: {len(work_df)} of {len(df)} rows (--max-rows).", flush=True)

    indexed = store.count()
    needs_build = rebuild or indexed < len(work_df)

    if needs_build:
        est_batches = (len(work_df) + 63) // 64
        print(
            "Building vector index on CPU (~1-2 hours for full 51k rows; progress every batch).",
            flush=True,
        )
        print(f"Batches to process: ~{est_batches}. Use --max-rows 5000 for a quicker test run.", flush=True)
        store.build_index(work_df, reset=rebuild, resume=not rebuild)
        print(f"Index ready: {store.count()} documents in Chroma.", flush=True)
    else:
        print(f"Using existing vector index ({indexed} documents).", flush=True)


def run_interactive(df: pd.DataFrame, store: RestaurantVectorStore) -> None:
    print("\n=== Zomato AI — Phase 2 Hybrid Search CLI ===\n")
    print("Hard filters: location, cuisine, budget (low/medium/high), min rating")
    print("Soft query: natural language (e.g. quiet rooftop with good views)\n")

    location = input("Location (e.g. Banashankari, BTM): ").strip()
    cuisine = input("Cuisine (e.g. Italian, North Indian): ").strip()
    budget = input("Budget tier [low/medium/high] (optional): ").strip()
    rating_in = input("Minimum rating (e.g. 4.0, optional): ").strip()
    min_rating = float(rating_in) if rating_in else 0.0
    query = input("Soft preference / description: ").strip()

    print("\n--- Hybrid retrieval ---")
    candidates = hybrid_search(
        df=df,
        vector_store=store,
        location=location,
        cuisine=cuisine,
        budget_tier=budget,
        min_rating=min_rating,
        query=query,
    )

    if candidates.empty:
        print("No restaurants matched your hard filters. Try relaxing location, cuisine, or rating.")
        return

    print(f"Candidates after hybrid merge: {len(candidates)}")
    print(format_candidates_preview(candidates))

    print("\n--- LLM ranking & explanations ---")
    response = get_recommendations(candidates_df=candidates, user_description=query)

    for i, rec in enumerate(response.recommendations, 1):
        print(f"\n{i}. {rec.name} — {rec.rating}★ | ₹{rec.cost} for two")
        print(f"   {rec.cuisines} @ {rec.location}")
        print(f"   {rec.explanation}")


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Hybrid semantic restaurant search")
    parser.add_argument("--ingest", action="store_true", help="Re-run Hugging Face ingestion")
    parser.add_argument("--build-index", action="store_true", help="Build or rebuild Chroma index")
    parser.add_argument("--rebuild-index", action="store_true", help="Drop and rebuild vector index")
    parser.add_argument(
        "--max-rows",
        type=int,
        default=INDEX_MAX_ROWS,
        help="Index only first N rows (faster test; omit for full dataset)",
    )
    parser.add_argument("--query", type=str, default="", help="Soft natural-language query")
    parser.add_argument("--location", type=str, default="")
    parser.add_argument("--cuisine", type=str, default="")
    parser.add_argument("--budget", type=str, default="")
    parser.add_argument("--min-rating", type=float, default=0.0)
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM; print hybrid results only")
    args = parser.parse_args()

    if args.ingest:
        run_ingestion()
        return

    df = load_dataset()
    store = RestaurantVectorStore()

    if args.build_index or args.rebuild_index:
        ensure_index(df, store, rebuild=args.rebuild_index, max_rows=args.max_rows)
        return

    ensure_index(df, store, rebuild=False, max_rows=args.max_rows)

    has_cli_filters = any([args.location, args.cuisine, args.budget, args.min_rating, args.query])
    if has_cli_filters:
        candidates = hybrid_search(
            df=df,
            vector_store=store,
            location=args.location,
            cuisine=args.cuisine,
            budget_tier=args.budget,
            min_rating=args.min_rating,
            query=args.query,
        )
        print(f"Hybrid matches: {len(candidates)}")
        print(format_candidates_preview(candidates, max_rows=10))
        if not args.no_llm and not candidates.empty:
            response = get_recommendations(candidates_df=candidates, user_description=args.query)
            for i, rec in enumerate(response.recommendations, 1):
                print(f"\n{i}. {rec.name} — {rec.explanation}")
        return

    run_interactive(df, store)


if __name__ == "__main__":
    main()
