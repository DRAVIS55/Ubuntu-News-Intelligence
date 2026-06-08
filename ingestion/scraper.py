"""
ingestion/scraper.py — Layer 1: Fetch articles from African news sources
Handles RSS feeds, web scraping, and NewsAPI sources.
Updated to use Django ORM instead of SQLAlchemy.
"""

import logging
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from core.config import config, NEWS_SOURCES
from core.models import Article, IngestionLog

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "AfricanNewsIntelPlatform/1.0 (+https://github.com/your-org/african-news-intel)"
}
REQUEST_TIMEOUT = 15


def _make_chroma_id(url: str, title: str) -> str:
    """Stable unique ID for vector DB based on source URL + title."""
    raw = f"{url}:{title}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


def _clean_html(raw_html: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    soup = BeautifulSoup(raw_html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _count_words(text: str) -> int:
    return len(text.split())


def fetch_rss_feed(source: dict) -> list[dict]:
    """
    Fetch and parse an RSS/Atom feed.
    Returns a list of article dicts ready for storage.
    """
    articles = []
    url = source["url"]
    logger.debug(f"Fetching RSS: {url}")

    try:
        feed = feedparser.parse(url, request_headers=HEADERS)
        if feed.bozo and not feed.entries:
            logger.warning(f"RSS parse error for {url}: {feed.bozo_exception}")
            return []

        for entry in feed.entries[:50]:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "")
            if not title or not link:
                continue

            body = ""
            if hasattr(entry, "content") and entry.content:
                body = _clean_html(entry.content[0].get("value", ""))
            elif hasattr(entry, "summary"):
                body = _clean_html(entry.summary)

            if not body or len(body) < 50:
                body = _scrape_article_body(link) or body

            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)

            author = getattr(entry, "author", None)

            articles.append({
                "source_name": source["name"],
                "source_url": link,
                "title": title[:500],
                "body": body[:50000],
                "author": author,
                "published_at": published_at,
                "country_code": source.get("country", "UNKNOWN"),
                "category": source.get("category", "general"),
                "language": source.get("language", "en"),
                "chroma_id": _make_chroma_id(link, title),
            })

    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")

    logger.info(f"[{source['name']}] {len(articles)} articles fetched")
    return articles


def _scrape_article_body(url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[str]:
    """Minimal article body scraper."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")

        selectors = [
            "article",
            '[class*="article-body"]',
            '[class*="story-body"]',
            '[class*="post-content"]',
            "main",
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 200:
                return _clean_html(str(el))

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs)
        if len(text) > 200:
            return text

    except Exception as e:
        logger.debug(f"Scrape failed for {url}: {e}")
    return None


def store_articles(articles: list[dict]) -> tuple[int, int]:
    """
    Persist a list of article dicts to the database using Django ORM.
    Skips duplicates (by chroma_id).

    Returns: (stored_count, skipped_count)
    """
    stored = 0
    skipped = 0

    existing_ids = set(Article.objects.values_list("chroma_id", flat=True))

    for data in articles:
        if data["chroma_id"] in existing_ids:
            skipped += 1
            continue

        Article.objects.create(
            source_name=data["source_name"],
            source_url=data["source_url"],
            title=data["title"],
            body=data["body"],
            author=data.get("author"),
            published_at=data["published_at"],
            country_code=data.get("country_code"),
            category=data.get("category"),
            language=data.get("language", "en"),
            chroma_id=data["chroma_id"],
            word_count=_count_words(data["body"]),
            is_processed=False,
        )
        stored += 1
        existing_ids.add(data["chroma_id"])

    logger.info(f"Stored {stored} new articles, skipped {skipped} duplicates")
    return stored, skipped


def run_ingestion(sources: Optional[list] = None) -> IngestionLog:
    """
    Main ingestion pipeline. Fetches all sources and stores new articles.
    """
    sources = sources or NEWS_SOURCES
    log = IngestionLog.objects.create(sources_attempted=len(sources), status="running")

    all_articles = []
    errors = []

    for source in sources:
        try:
            fetched = fetch_rss_feed(source)
            all_articles.extend(fetched)
        except Exception as e:
            errors.append({"source": source["name"], "error": str(e)})
            logger.error(f"Source failed [{source['name']}]: {e}")

    stored_count, _ = store_articles(all_articles)

    log.articles_fetched = len(all_articles)
    log.articles_stored = stored_count
    log.completed_at = datetime.now(timezone.utc)
    log.status = "success" if not errors else "partial"
    log.errors = errors
    log.save()

    logger.info(f"Ingestion complete: {len(all_articles)} fetched, {stored_count} stored")
    return log
