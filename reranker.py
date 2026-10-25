# reranker.py
import re
from typing import Any, Dict, List, Optional
import numpy as np

# Global cache for sentence transformer models to avoid expensive reloads
_MODEL_CACHE: Dict[str, Any] = {}


def get_sentence_transformer(model_name: str = "all-MiniLM-L6-v2"):
    """Get or load a SentenceTransformer model from memory cache."""
    global _MODEL_CACHE
    if model_name not in _MODEL_CACHE:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
        except Exception as e:
            print(f"Warning: Could not load SentenceTransformer '{model_name}': {e}")
            _MODEL_CACHE[model_name] = None
    return _MODEL_CACHE[model_name]


class Reranker:
    """Semantic and lexical reranker for retrieved documents."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        top_k: int = 3,
        max_chars: int = 3000
    ):
        self.model_name = model_name
        self.top_k = top_k
        self.max_chars = max_chars
        self._model = None

    @property
    def model(self):
        """Lazy load model on first usage."""
        if self._model is None:
            self._model = get_sentence_transformer(self.model_name)
        return self._model

    def _fallback_lexical_rank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback keyword overlap ranking if neural model is unavailable."""
        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words:
            return results[:self.top_k]

        scored = []
        for r in results:
            content = r.get("content", "") + " " + r.get("title", "")
            words = re.findall(r"\w+", content.lower())
            overlap = sum(1 for w in words if w in query_words)
            score = overlap / (len(words) + 1e-5)
            doc_copy = dict(r)
            doc_copy["relevance_score"] = float(score)
            scored.append(doc_copy)

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:self.top_k]

    def rank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank retrieved documents by semantic similarity to the query.

        Args:
            query: User's search query.
            results: List of retrieved document dictionaries.

        Returns:
            Top-K ranked document dictionaries with relevance scores.
        """
        if not results:
            return []

        if not query or not str(query).strip():
            # Return top-k unmodified if query is blank
            return [dict(r) for r in results[:self.top_k]]

        # Filter valid documents with non-trivial text
        valid_results = []
        for r in results:
            content = r.get("content", "")
            title = r.get("title", "")
            if (content and len(content.strip()) > 15) or (title and len(title.strip()) > 5):
                valid_results.append(r)

        if not valid_results:
            return []

        # If neural model is not available, use lexical ranking
        if self.model is None:
            return self._fallback_lexical_rank(query, valid_results)

        try:
            # 1. Query embedding (shape: [D])
            query_embedding = self.model.encode(
                query,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            # 2. Document embeddings (batch encoded)
            documents = [
                f"{r.get('title', '')}\n{r.get('content', '')[:1000]}".strip()
                for r in valid_results
            ]

            document_embeddings = self.model.encode(
                documents,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=min(32, len(documents))
            )

            # 3. Cosine similarity
            scores = np.dot(document_embeddings, query_embedding)
            # Ensure 1D array even if single result
            scores = np.atleast_1d(scores)

            # 4. Attach relevance scores safely without mutating originals
            scored_results = []
            for result, score in zip(valid_results, scores):
                doc_copy = dict(result)
                doc_copy["relevance_score"] = round(float(score), 4)
                scored_results.append(doc_copy)

            # 5. Sort by relevance descending
            scored_results.sort(
                key=lambda x: x["relevance_score"],
                reverse=True
            )

            # 6. Keep TOP K
            top_results = scored_results[:self.top_k]

            # 7. Truncate document size for LLM context optimization
            for doc in top_results:
                content = doc.get("content", "")
                if len(content) > self.max_chars:
                    doc["content"] = (
                        content[:self.max_chars]
                        + "\n...[Content truncated for length]"
                    )

            return top_results

        except Exception as e:
            print(f"Neural reranking failed ({e}), falling back to lexical ranking.")
            return self._fallback_lexical_rank(query, valid_results)
