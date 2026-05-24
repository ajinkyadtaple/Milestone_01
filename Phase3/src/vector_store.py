from __future__ import annotations

from src.config import CHROMA_COLLECTION, CHROMA_DIR


class NullVectorStore:
    """Fallback when Chroma is missing or corrupt — structured search only."""

    def count(self) -> int:
        return 0

    def query_similar(self, *args, **kwargs) -> list[dict]:
        return []


class RestaurantVectorStore:
    def __init__(self, persist_dir=None, collection_name: str = CHROMA_COLLECTION):
        import chromadb
        from chromadb.config import Settings

        self.persist_dir = persist_dir or CHROMA_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder = None

    @property
    def embedder(self):
        if self._embedder is None:
            from src.embeddings import EmbeddingService

            self._embedder = EmbeddingService()
        return self._embedder

    def count(self) -> int:
        try:
            return self.collection.count()
        except Exception:
            return 0

    def query_similar(
        self,
        query_text: str,
        restaurant_ids: list[str] | None = None,
        n_results: int = 15,
    ) -> list[dict]:
        query_text = (query_text or "").strip()
        if not query_text or self.count() == 0:
            return []

        try:
            query_embedding = self.embedder.embed_query(query_text)
            if not query_embedding:
                return []

            if not restaurant_ids:
                result = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    include=["metadatas", "distances"],
                )
                return self._format_query_result(result)

            return self._rank_within_ids(query_embedding, restaurant_ids, n_results)
        except Exception as e:
            print(f"Vector search unavailable ({e}); falling back to filter-only ranking.")
            return []

    def _rank_within_ids(
        self,
        query_embedding: list[float],
        restaurant_ids: list[str],
        n_results: int,
    ) -> list[dict]:
        import numpy as np

        q = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []

        scored: list[tuple[float, str, dict]] = []
        for start in range(0, len(restaurant_ids), 500):
            chunk = restaurant_ids[start : start + 500]
            batch = self.collection.get(ids=chunk, include=["embeddings", "metadatas"])
            if not batch["ids"]:
                continue
            for i, rid in enumerate(batch["ids"]):
                emb = batch["embeddings"][i]
                if emb is None:
                    continue
                vec = np.array(emb, dtype=np.float32)
                denom = np.linalg.norm(vec) * q_norm
                similarity = float(np.dot(vec, q) / denom) if denom else 0.0
                meta = batch["metadatas"][i] if batch.get("metadatas") else {}
                scored.append((1.0 - similarity, rid, meta))

        scored.sort(key=lambda x: x[0])
        return [
            {"restaurant_id": rid, "distance": dist, "metadata": meta, "document": ""}
            for dist, rid, meta in scored[:n_results]
        ]

    @staticmethod
    def _format_query_result(result: dict) -> list[dict]:
        matches: list[dict] = []
        if not result["ids"] or not result["ids"][0]:
            return matches
        for i, rid in enumerate(result["ids"][0]):
            matches.append(
                {
                    "restaurant_id": rid,
                    "distance": result["distances"][0][i] if result.get("distances") else None,
                    "metadata": result["metadatas"][0][i] if result.get("metadatas") else {},
                    "document": "",
                }
            )
        return matches
