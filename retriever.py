import hashlib
import re

import numpy as np
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Shared model — loaded ONCE for the entire app, not once per service.
# This saves ~400MB RAM per service (5 services = ~2GB saved).
# ---------------------------------------------------------------------------
_shared_model: SentenceTransformer | None = None

# Query embedding cache — avoids re-encoding identical queries
_query_cache: dict[str, np.ndarray] = {}

def _get_model() -> SentenceTransformer:
    global _shared_model
    if _shared_model is None:
        _shared_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _shared_model


def _cache_key(text: str) -> str:
    """Generate a cache key for a query string."""
    return hashlib.md5(text.strip().encode()).hexdigest()


def _get_query_embedding(text: str) -> np.ndarray:
    """Get (or compute and cache) the embedding for a query."""
    key = _cache_key(text)
    if key in _query_cache:
        return _query_cache[key]

    model = _get_model()
    embedding = model.encode(text.strip(), normalize_embeddings=True, show_progress_bar=False)
    _query_cache[key] = embedding
    return embedding


def _token_overlap_score(query: str, doc: str) -> float:
    """Lightweight lexical overlap score for hybrid retrieval."""
    query_tokens = {token for token in re.findall(r"[a-z0-9]+", query.lower()) if len(token) >= 3}
    doc_tokens = {token for token in re.findall(r"[a-z0-9]+", doc.lower()) if len(token) >= 3}
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & doc_tokens)
    return round(overlap / max(1, len(query_tokens)), 3)


class Retriever:
    def __init__(self, docs: list[str], source_domain: str = ""):
        """
        Build a retriever for a list of knowledge-base doc strings.
        Embeddings are computed once at init and reused for all queries.
        Uses the shared model — so 5 Retrievers still only load 1 model.
        """
        model = _get_model()
        self.source_domain = source_domain

        # Strip whitespace, drop blank lines
        self.docs = [d.strip() for d in docs if d.strip()]

        if self.docs:
            # normalize_embeddings=True → vectors are unit-length
            # → dot product IS cosine similarity (no extra math needed)
            self.doc_embeddings = model.encode(
                self.docs,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        else:
            self.doc_embeddings = np.array([])

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """
        Return the top_k most semantically similar docs to the query.
        Returns empty list if no docs are loaded.

        Backward-compatible: returns list[str] for existing consumers.
        """
        results = self.retrieve_with_scores(query, top_k)
        return [r["text"] for r in results]

    def retrieve_with_scores(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Return top_k docs with relevance scores and source attribution.

        Returns:
            List of dicts: [
                {
                    "text": str,
                    "score": float,        # cosine similarity 0-1
                    "source": str,         # source domain name
                    "reason": str,         # human-readable retrieval explanation
                },
                ...
            ]
        """
        if not self.docs or self.doc_embeddings.size == 0:
            return []

        # Use cached query embedding
        query_embedding = _get_query_embedding(query)

        # Cosine similarities — shape: (num_docs,)
        similarities = np.dot(self.doc_embeddings, query_embedding)

        # Lightweight lexical overlap boosts precision for keyword-heavy tickets.
        overlap_scores = np.array([_token_overlap_score(query, doc) for doc in self.docs], dtype=float)
        hybrid_scores = 0.7 * similarities + 0.3 * overlap_scores
        hybrid_scores = np.clip(hybrid_scores, 0.0, 1.0)

        # Take top_k, sorted by score descending
        k = min(top_k, len(self.docs))
        top_indices = hybrid_scores.argsort()[-k:][::-1]

        # Higher minimum threshold for better precision
        MIN_SIMILARITY = 0.25

        results = []
        for i in top_indices:
            score = float(hybrid_scores[i])
            if score >= MIN_SIMILARITY:
                if score >= 0.6:
                    relevance = "Highly relevant"
                elif score >= 0.4:
                    relevance = "Moderately relevant"
                else:
                    relevance = "Partially relevant"

                results.append({
                    "text": self.docs[i],
                    "score": round(score, 3),
                    "source": self.source_domain,
                    "reason": f"{relevance} — similarity score {score:.0%} to your query"
                              f"{f' from {self.source_domain} knowledge base' if self.source_domain else ''}.",
                })

        return results