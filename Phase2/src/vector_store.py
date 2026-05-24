from __future__ import annotations

import pandas as pd
import chromadb
from chromadb.config import Settings

from src.config import CHROMA_COLLECTION, CHROMA_DIR, EMBED_BATCH_SIZE
from src.embeddings import EmbeddingService, documents_from_dataframe


class RestaurantVectorStore:
    """ChromaDB-backed index for restaurant semantic search."""

    def __init__(self, persist_dir=None, collection_name: str = CHROMA_COLLECTION):
        self.persist_dir = persist_dir or CHROMA_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder: EmbeddingService | None = None

    @property
    def embedder(self) -> EmbeddingService:
        if self._embedder is None:
            self._embedder = EmbeddingService()
        return self._embedder

    def count(self) -> int:
        return self.collection.count()

    def build_index(
        self,
        df: pd.DataFrame,
        batch_size: int = EMBED_BATCH_SIZE,
        reset: bool = False,
        resume: bool = True,
    ) -> int:
        """Embed all rows and upsert into Chroma. Returns number of indexed documents."""
        if reset and self.count() > 0:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        ids, documents, metadatas = documents_from_dataframe(df)
        already_indexed: set[str] = set()
        if resume and not reset and self.count() > 0:
            offset = 0
            page = 5000
            while True:
                chunk = self.collection.get(
                    limit=page,
                    offset=offset,
                    include=[],
                )
                if not chunk["ids"]:
                    break
                already_indexed.update(chunk["ids"])
                if len(chunk["ids"]) < page:
                    break
                offset += page
            if already_indexed:
                print(
                    f"Resuming index: {len(already_indexed)} already in Chroma, skipping those rows.",
                    flush=True,
                )

        total = len(already_indexed)
        target = len(ids)

        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            batch_ids = ids[start:end]
            if resume and already_indexed and all(i in already_indexed for i in batch_ids):
                continue

            pending = [
                (i, d, m)
                for i, d, m in zip(
                    batch_ids,
                    documents[start:end],
                    metadatas[start:end],
                )
                if i not in already_indexed
            ]
            if not pending:
                continue

            p_ids, p_docs, p_meta = zip(*pending)
            print(f"Embedding batch starting at row {start}...", flush=True)
            batch_embeddings = self.embedder.embed_texts(list(p_docs), batch_size=batch_size)

            self.collection.upsert(
                ids=list(p_ids),
                documents=list(p_docs),
                metadatas=list(p_meta),
                embeddings=batch_embeddings,
            )
            total += len(p_ids)
            print(f"Indexed {total}/{target} restaurants...", flush=True)

        return total

    def query_similar(
        self,
        query_text: str,
        restaurant_ids: list[str] | None = None,
        n_results: int = 15,
    ) -> list[dict]:
        """
        Return top semantic matches. When restaurant_ids is provided, score only
        that pre-filtered subset (supports large filter results via batched gets).
        """
        query_text = (query_text or "").strip()
        if not query_text:
            return []

        query_embedding = self.embedder.embed_query(query_text)
        if not query_embedding:
            return []

        if not restaurant_ids:
            result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "documents", "distances"],
            )
            return self._format_query_result(result)

        return self._rank_within_ids(query_embedding, restaurant_ids, n_results)

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
        batch_size = 500

        for start in range(0, len(restaurant_ids), batch_size):
            chunk = restaurant_ids[start : start + batch_size]
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
                distance = 1.0 - similarity
                meta = batch["metadatas"][i] if batch.get("metadatas") else {}
                scored.append((distance, rid, meta))

        scored.sort(key=lambda x: x[0])
        matches: list[dict] = []
        for distance, rid, meta in scored[:n_results]:
            matches.append(
                {
                    "restaurant_id": rid,
                    "distance": distance,
                    "metadata": meta,
                    "document": "",
                }
            )
        return matches

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
                    "document": result["documents"][0][i] if result.get("documents") else "",
                }
            )
        return matches
