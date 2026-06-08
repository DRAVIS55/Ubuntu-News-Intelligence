"""
ingestion/embedder.py — Generate and store vector embeddings for all articles
Uses sentence-transformers to embed article text into ChromaDB.
Updated to use Django ORM instead of SQLAlchemy.
"""

import logging
from typing import Optional
from sentence_transformers import SentenceTransformer

from core.config import config
from core.database import get_articles_collection
from core.models import Article

logger = logging.getLogger(__name__)

_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Load (once) the sentence embedding model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("Embedding model loaded.")
    return _model


def embed_text(text: str) -> list[float]:
    """Convert text to a float vector."""
    model = get_embedding_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def embed_articles(batch_size: int = 32) -> int:
    """
    Find all unprocessed articles in the DB, generate embeddings,
    store them in ChromaDB, and mark articles as processed.

    Returns: number of articles embedded
    """
    collection = get_articles_collection()
    model = get_embedding_model()

    total_embedded = 0

    unprocessed = list(
        Article.objects
        .filter(is_processed=False)
        .order_by("-published_at")[:config.MAX_ARTICLES_PER_RUN]
    )

    if not unprocessed:
        logger.info("No unprocessed articles found.")
        return 0

    logger.info(f"Embedding {len(unprocessed)} articles...")

    for i in range(0, len(unprocessed), batch_size):
        batch = unprocessed[i: i + batch_size]

        texts = [f"{article.title}. {article.body[:2000]}" for article in batch]

        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

        ids = [a.chroma_id for a in batch]
        metadatas = [
            {
                "article_id": str(a.id),
                "title": a.title[:200],
                "source_name": a.source_name,
                "country_code": a.country_code or "",
                "category": a.category or "",
                "language": a.language or "en",
                "published_at": a.published_at.isoformat() if a.published_at else "",
            }
            for a in batch
        ]
        documents = [f"{a.title}. {a.body[:500]}" for a in batch]

        try:
            collection.upsert(
                ids=ids,
                embeddings=[e.tolist() for e in embeddings],
                metadatas=metadatas,
                documents=documents,
            )
        except Exception as e:
            logger.error(f"ChromaDB upsert failed for batch {i}: {e}")
            continue

        # Mark as processed (bulk update via Django ORM)
        ids_to_mark = [a.id for a in batch]
        Article.objects.filter(id__in=ids_to_mark).update(is_processed=True)

        total_embedded += len(batch)
        logger.debug(f"Embedded batch {i // batch_size + 1} ({total_embedded} total)")

    logger.info(f"Embedding complete: {total_embedded} articles embedded")
    return total_embedded


def semantic_search(
    query: str,
    n_results: int = 10,
    country_code: Optional[str] = None,
    category: Optional[str] = None,
) -> list[dict]:
    """
    Search the archive semantically.
    Returns ranked list of matching articles with similarity scores.
    """
    collection = get_articles_collection()

    where = {}
    if country_code and category:
        where = {"$and": [{"country_code": country_code}, {"category": category}]}
    elif country_code:
        where = {"country_code": country_code}
    elif category:
        where = {"category": category}

    query_embedding = embed_text(query)

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count() or 1),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    results = collection.query(**query_kwargs)

    output = []
    for i, (doc, meta, dist) in enumerate(
        zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ):
        similarity = 1 - dist
        output.append(
            {
                "rank": i + 1,
                "similarity": round(similarity, 4),
                "title": meta.get("title", ""),
                "source_name": meta.get("source_name", ""),
                "country_code": meta.get("country_code", ""),
                "category": meta.get("category", ""),
                "published_at": meta.get("published_at", ""),
                "article_id": meta.get("article_id", ""),
                "snippet": doc[:300],
                "chroma_id": results["ids"][0][i],
            }
        )

    return output
