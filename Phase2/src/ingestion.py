import ast
import re
import pandas as pd
from datasets import load_dataset
from src.config import ENRICHED_DATA_PATH


def clean_rating(val):
    if not val or not isinstance(val, str):
        return 0.0
    val = val.strip()
    if "/" in val:
        parts = val.split("/")
        try:
            return float(parts[0].strip())
        except ValueError:
            return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0


def clean_cost(val):
    if not val or not isinstance(val, str):
        return None
    val = val.replace(",", "").strip()
    try:
        return int(val)
    except ValueError:
        return None


def extract_review_snippets(reviews_raw, max_reviews: int = 2, max_chars: int = 200) -> str:
    """Parse reviews_list field into a compact text snippet for embeddings."""
    if not reviews_raw or not isinstance(reviews_raw, str):
        return ""

    texts: list[str] = []
    try:
        reviews = ast.literal_eval(reviews_raw)
        for item in reviews[:max_reviews]:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                body = str(item[1]).replace("RATED\n", "").replace("RATED", "").strip()
                body = re.sub(r"\s+", " ", body)
                texts.append(body[:max_chars])
    except (SyntaxError, ValueError):
        for match in re.finditer(r"'RATED\\n',\s*'([^']{20,})'", reviews_raw):
            texts.append(match.group(1)[:max_chars])
            if len(texts) >= max_reviews:
                break

    return " | ".join(texts)


def build_search_text(row: pd.Series) -> str:
    """Combine structured fields and review snippets into one searchable document."""
    parts = [
        f"Restaurant: {row.get('name', '')}.",
        f"Type: {row.get('rest_type', '')}.",
        f"Cuisines: {row.get('cuisines', '')}.",
        f"Popular dishes: {row.get('dish_liked', '')}.",
        f"Location: {row.get('location', '')}.",
        f"Address: {row.get('address', '')}.",
        f"Listed as: {row.get('listed_in_type', '')}.",
        f"Online order: {row.get('online_order', '')}. Table booking: {row.get('book_table', '')}.",
    ]
    reviews = row.get("review_snippet", "")
    if reviews:
        parts.append(f"Customer reviews: {reviews}")
    return " ".join(p for p in parts if p and str(p).strip() not in ("", "nan", "None."))


def run_ingestion() -> pd.DataFrame:
    print("Phase 2 ingestion: fetching dataset from Hugging Face...")
    dataset = load_dataset("ManikaSaini/zomato-restaurant-recommendation")
    df = dataset["train"].to_pandas()
    print(f"Raw shape: {df.shape}")

    df["rate_float"] = df["rate"].apply(clean_rating)
    df["cost_clean"] = df["approx_cost(for two people)"].apply(clean_cost)
    median_cost = df["cost_clean"].median()
    if pd.isna(median_cost):
        median_cost = 500
    df["cost_clean"] = df["cost_clean"].fillna(median_cost).astype(int)
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

    df["location_clean"] = df["location"].fillna("").astype(str).str.strip().str.lower()
    df["cuisines_clean"] = df["cuisines"].fillna("").astype(str).str.strip().str.lower()
    df["name"] = df["name"].fillna("Unknown Restaurant").astype(str).str.strip()

    df["rest_type"] = df["rest_type"].fillna("").astype(str).str.strip()
    df["dish_liked"] = df["dish_liked"].fillna("").astype(str).str.strip()
    df["listed_in_type"] = df["listed_in(type)"].fillna("").astype(str).str.strip()

    print("Extracting review snippets for semantic search...")
    df["review_snippet"] = df["reviews_list"].apply(extract_review_snippets)
    df["search_text"] = df.apply(build_search_text, axis=1)

    cols_to_keep = [
        "name",
        "rate_float",
        "cost_clean",
        "votes",
        "location",
        "location_clean",
        "cuisines",
        "cuisines_clean",
        "address",
        "online_order",
        "book_table",
        "rest_type",
        "dish_liked",
        "listed_in_type",
        "review_snippet",
        "search_text",
    ]
    df_cleaned = df[cols_to_keep].reset_index(drop=True)
    df_cleaned["restaurant_id"] = df_cleaned.index.astype(str)

    df_cleaned.to_csv(ENRICHED_DATA_PATH, index=False, encoding="utf-8")
    print(f"Enriched dataset saved: {ENRICHED_DATA_PATH} (rows={len(df_cleaned)})")
    return df_cleaned


if __name__ == "__main__":
    run_ingestion()
