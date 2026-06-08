"""
run.py — Application entry point
Starts the Django app with the background ingestion scheduler
"""

import logging
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from core.config import config

# ── Logging ────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(config.LOG_FILE) if os.path.dirname(config.LOG_FILE) else ".", exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main():
    from core.database import init_db
    from ingestion.scheduler import start_scheduler
    from django.core.management import call_command

    logger.info("=" * 60)
    logger.info("  African News Intelligence Platform")
    logger.info("  Built in Nairobi. For African journalism.")
    logger.info("  Framework: Django")
    logger.info("=" * 60)

    # Initialise relational database (ChromaDB + SQLite/Postgres)
    logger.info("Initialising database...")
    init_db()

    # Run Django migrations
    logger.info("Running Django migrations...")
    call_command("migrate", "--run-syncdb", verbosity=0)

    # Start background scheduler
    logger.info("Starting ingestion scheduler...")
    start_scheduler()

    # Run Django dev server
    logger.info(f"Starting Django server on http://0.0.0.0:{config.PORT}")
    call_command("runserver", f"0.0.0.0:{config.PORT}", use_reloader=False)


if __name__ == "__main__":
    main()
