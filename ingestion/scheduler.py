"""
ingestion/scheduler.py — Background ingestion scheduler
Runs scraping + embedding on a configurable interval.
APScheduler is framework-agnostic; works identically under Django.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.config import config
from ingestion.scraper import run_ingestion
from ingestion.embedder import embed_articles
from intelligence.relations import run_relation_engine
from intelligence.patterns import run_pattern_detection

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def run_full_pipeline():
    """
    Full pipeline run:
    1. Scrape all sources
    2. Generate embeddings for new articles
    3. Build article relations
    4. Detect patterns
    """
    logger.info("=== Pipeline run started ===")

    try:
        log = run_ingestion()
        logger.info(f"Ingestion: {log.articles_stored} new articles")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return

    try:
        embedded = embed_articles()
        logger.info(f"Embedding: {embedded} articles embedded")
    except Exception as e:
        logger.error(f"Embedding failed: {e}")

    try:
        run_relation_engine()
        logger.info("Relation engine complete")
    except Exception as e:
        logger.error(f"Relation engine failed: {e}")

    try:
        run_pattern_detection()
        logger.info("Pattern detection complete")
    except Exception as e:
        logger.error(f"Pattern detection failed: {e}")

    logger.info("=== Pipeline run complete ===")


def start_scheduler():
    """Start the background scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        logger.warning("Scheduler already running")
        return

    _scheduler = BackgroundScheduler(timezone="Africa/Nairobi")
    _scheduler.add_job(
        func=run_full_pipeline,
        trigger=IntervalTrigger(minutes=config.INGESTION_INTERVAL_MINUTES),
        id="full_pipeline",
        name="Full ingestion + processing pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info(
        f"Scheduler started — pipeline runs every {config.INGESTION_INTERVAL_MINUTES} minutes"
    )


def stop_scheduler():
    """Gracefully stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def trigger_now():
    """Manually trigger a pipeline run immediately."""
    import threading
    thread = threading.Thread(target=run_full_pipeline, daemon=True)
    thread.start()
    return thread
