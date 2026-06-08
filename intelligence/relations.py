"""
intelligence/relations.py — Layer 2c: Article Relation Engine
Automatically links new articles to historically similar events.
Updated to use Django ORM instead of SQLAlchemy.
"""

import logging
import spacy
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.models import Article, ArticleRelation

logger = logging.getLogger(__name__)

_nlp: Optional[spacy.language.Language] = None


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded")
        except OSError:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            _nlp = None
    return _nlp


def extract_entities(text: str) -> dict:
    """
    Extract named entities from article text.
    Returns dict with entity types as keys.
    """
    nlp = get_nlp()
    if not nlp:
        return {}

    doc = nlp(text[:5000])
    entities = {
        "persons": [],
        "organisations": [],
        "places": [],
        "amounts": [],
        "dates": [],
        "other": [],
    }

    type_map = {
        "PERSON": "persons",
        "ORG": "organisations",
        "GPE": "places",
        "LOC": "places",
        "MONEY": "amounts",
        "PERCENT": "amounts",
        "DATE": "dates",
        "TIME": "dates",
    }

    for ent in doc.ents:
        category = type_map.get(ent.label_, "other")
        text_val = ent.text.strip()
        if text_val and text_val not in entities[category]:
            entities[category].append(text_val)

    return {k: v[:20] for k, v in entities.items()}


def find_historical_parallels(
    article: Article,
    n_results: int = 10,
    min_similarity: float = 0.55,
    max_age_years: int = 20,
) -> list[dict]:
    """
    Find historically similar articles for a given article.
    """
    from ingestion.embedder import semantic_search

    query = f"{article.title}. {article.body[:500]}"
    candidates = semantic_search(query, n_results=n_results + 1)

    results = []
    for c in candidates:
        if c.get("article_id") and int(c["article_id"]) == article.id:
            continue
        if c["similarity"] < min_similarity:
            continue

        try:
            pub_date = datetime.fromisoformat(c["published_at"])
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=365 * max_age_years)
            if pub_date < cutoff:
                continue
        except Exception:
            pass

        results.append(c)

    return results[:n_results]


def store_relations(article: Article, parallels: list[dict]) -> int:
    """
    Persist ArticleRelation records for detected parallels.
    Returns number stored.
    """
    stored = 0
    for p in parallels:
        target_id_str = p.get("article_id")
        if not target_id_str:
            continue

        target_id = int(target_id_str)

        exists = ArticleRelation.objects.filter(
            source_id=article.id, target_id=target_id
        ).exists()
        if exists:
            continue

        try:
            ArticleRelation.objects.create(
                source_id=article.id,
                target_id=target_id,
                similarity_score=p["similarity"],
                relation_type="historical_parallel",
                context_note=(
                    f"Semantic similarity: {p['similarity']:.2f}. "
                    f"Historical article from {p.get('published_at', 'unknown date')}."
                ),
            )
            stored += 1
        except Exception as e:
            logger.warning(f"Could not store relation {article.id} → {target_id}: {e}")

    return stored


def run_relation_engine(batch_size: int = 50) -> int:
    """
    Process recently ingested articles, extract entities, and build relations.
    Returns total relations created.
    """
    nlp = get_nlp()
    total_relations = 0

    recent = (
        Article.objects
        .filter(entity_tags__isnull=True, is_processed=True)
        .order_by("-published_at")[:batch_size]
    )

    articles = list(recent)
    if not articles:
        logger.info("Relation engine: no new articles to process")
        return 0

    logger.info(f"Relation engine: processing {len(articles)} articles")

    for article in articles:
        if nlp and article.body:
            entities = extract_entities(f"{article.title} {article.body}")
            article.entity_tags = entities
            article.save(update_fields=["entity_tags"])

        parallels = find_historical_parallels(article)
        if parallels:
            n = store_relations(article, parallels)
            total_relations += n

    logger.info(f"Relation engine complete: {total_relations} relations created")
    return total_relations


def get_article_parallels(article_id: int, min_similarity: float = 0.6) -> list[dict]:
    """
    Retrieve stored historical parallels for a given article ID.
    """
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return []

    relations = (
        ArticleRelation.objects
        .filter(source_id=article_id, similarity_score__gte=min_similarity)
        .select_related("target")
        .order_by("-similarity_score")[:10]
    )

    result = []
    for rel in relations:
        target = rel.target
        result.append({
            "article_id": target.id,
            "title": target.title,
            "source_name": target.source_name,
            "published_at": target.published_at.isoformat() if target.published_at else None,
            "country_code": target.country_code,
            "similarity_score": rel.similarity_score,
            "relation_type": rel.relation_type,
            "context_note": rel.context_note,
            "snippet": target.body[:300],
        })

    return result
