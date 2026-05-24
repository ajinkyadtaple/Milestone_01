from __future__ import annotations

import pandas as pd
from sentence_transformers import SentenceTransformer

from src.config import EMBED_BATCH_SIZE, EMBEDDING_MODEL, MAX_INDEX_TEXT_CHARS


class EmbeddingService:
    """Local dense embeddings for restaurant documents and user queries."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str], batch_size: int = EMBED_BATCH_SIZE) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 500,
            convert_to_numpy=True,
        )
        return vectors.tolist()

    def embed_query(self, query: str) -> list[float]:
        query = (query or "").strip()
        if not query:
            return []
        return self.model.encode(query, convert_to_numpy=True).tolist()


def documents_from_dataframe(df: pd.DataFrame) -> tuple[list[str], list[str], list[dict]]:
    """Prepare ids, documents, and metadata for vector indexing."""
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for _, row in df.iterrows():
        rid = str(row["restaurant_id"])
        ids.append(rid)
        text = str(row["search_text"])
        if MAX_INDEX_TEXT_CHARS and len(text) > MAX_INDEX_TEXT_CHARS:
            text = text[:MAX_INDEX_TEXT_CHARS]
        documents.append(text)
        metadatas.append(
            {
                "restaurant_id": rid,
                "name": str(row["name"]),
                "location": str(row["location"]),
                "cuisines": str(row["cuisines"]),
                "rate_float": float(row["rate_float"]),
                "cost_clean": int(row["cost_clean"]),
            }
        )

    return ids, documents, metadatas
