"""
core/database.py — Database connections: Django ORM (PostgreSQL/SQLite) + ChromaDB

Django handles the relational DB via its ORM and migration system.
This module provides:
  - ChromaDB (vector DB) client and collection helpers
  - init_db() for ChromaDB initialisation at startup
  - health check utilities
"""

import logging
import chromadb
from chromadb.config import Settings
from contextlib import contextmanager

from core.config import config

logger = logging.getLogger(__name__)


def init_db():
    """
    Initialise ChromaDB at startup.
    Django migrations handle the relational DB separately via manage.py migrate.
    """
    get_articles_collection()
    logger.info("ChromaDB initialised.")


# ── ChromaDB (vector DB) ────────────────────────────────────────────────────────

_chroma_client: chromadb.Client | None = None
_articles_collection = None


def get_chroma_client() -> chromadb.Client:
    """Return (or initialise) the ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=config.CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info(f"ChromaDB initialised at {config.CHROMA_PATH}")
    return _chroma_client


def get_articles_collection():
    """Return (or create) the articles ChromaDB collection."""
    global _articles_collection
    if _articles_collection is None:
        client = get_chroma_client()
        _articles_collection = client.get_or_create_collection(
            name="articles",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB articles collection ready ({_articles_collection.count()} vectors)"
        )
    return _articles_collection


def health_check_db() -> bool:
    """Verify Django ORM DB is reachable."""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        return False


def health_check_chroma() -> bool:
    """Verify ChromaDB is reachable."""
    try:
        col = get_articles_collection()
        _ = col.count()
        return True
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        return False
