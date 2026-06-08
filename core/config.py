"""
core/config.py — Central configuration management
Loads from environment variables / .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


class Config:
    """Platform-wide configuration."""

    # ── Django ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DJANGO_ENV: str = os.getenv("DJANGO_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", 8000))
    ALLOWED_HOSTS: list = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///african_news_intel.db"
    )

    # ── Vector DB ──────────────────────────────────────────────────────────
    CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./data/chroma_db")

    # ── LLM ────────────────────────────────────────────────────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    LOCAL_MODEL_PATH: str = os.getenv("LOCAL_MODEL_PATH", "./models/mistral-7b.gguf")
    LOCAL_MODEL_N_CTX: int = int(os.getenv("LOCAL_MODEL_N_CTX", 8192))
    LOCAL_MODEL_N_GPU_LAYERS: int = int(os.getenv("LOCAL_MODEL_N_GPU_LAYERS", 0))

    # ── External APIs ──────────────────────────────────────────────────────
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    WORLD_BANK_API_KEY: str = os.getenv("WORLD_BANK_API_KEY", "")

    # ── Embeddings ─────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # ── Ingestion ──────────────────────────────────────────────────────────
    INGESTION_INTERVAL_MINUTES: int = int(
        os.getenv("INGESTION_INTERVAL_MINUTES", 30)
    )
    MAX_ARTICLES_PER_RUN: int = int(os.getenv("MAX_ARTICLES_PER_RUN", 200))

    # ── Pattern Detection ──────────────────────────────────────────────────
    PATTERN_DETECTION_WINDOW_DAYS: int = int(
        os.getenv("PATTERN_DETECTION_WINDOW_DAYS", 30)
    )
    PATTERN_MIN_OCCURRENCES: int = int(os.getenv("PATTERN_MIN_OCCURRENCES", 3))

    # ── Security ───────────────────────────────────────────────────────────
    API_RATE_LIMIT: str = os.getenv("API_RATE_LIMIT", "100 per hour")
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "dev-admin-token")

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./data/logs/anip.log")


# ── African News Sources ────────────────────────────────────────────────────────
NEWS_SOURCES = [
    # Kenya
    {"name": "Nation Africa", "url": "https://nation.africa/kenya/rss.xml", "country": "KE", "category": "general"},
    {"name": "The Standard", "url": "https://www.standardmedia.co.ke/rss/kenya.php", "country": "KE", "category": "general"},
    {"name": "Business Daily", "url": "https://businessdailyafrica.com/rss/all", "country": "KE", "category": "business"},
    {"name": "KBC", "url": "https://www.kbc.co.ke/feed/", "country": "KE", "category": "general"},
    # Pan-African
    {"name": "AllAfrica", "url": "https://allafrica.com/tools/headlines/rdf/east/headlines.rdf", "country": "MULTI", "category": "general"},
    {"name": "African Arguments", "url": "https://africanarguments.org/feed/", "country": "MULTI", "category": "politics"},
    # Tanzania
    {"name": "The Citizen TZ", "url": "https://www.thecitizen.co.tz/tanzania/rss.xml", "country": "TZ", "category": "general"},
    # Uganda
    {"name": "Daily Monitor UG", "url": "https://www.monitor.co.ug/uganda/rss.xml", "country": "UG", "category": "general"},
    # Rwanda
    {"name": "The New Times RW", "url": "https://www.newtimes.co.rw/rss.xml", "country": "RW", "category": "general"},
    # Ethiopia
    {"name": "Addis Standard", "url": "https://addisstandard.com/feed/", "country": "ET", "category": "general"},
]

# ── EAC Peer Countries ──────────────────────────────────────────────────────────
EAC_COUNTRIES = {
    "KE": {"name": "Kenya", "currency": "KES", "wb_code": "KEN"},
    "TZ": {"name": "Tanzania", "currency": "TZS", "wb_code": "TZA"},
    "UG": {"name": "Uganda", "currency": "UGX", "wb_code": "UGA"},
    "RW": {"name": "Rwanda", "currency": "RWF", "wb_code": "RWA"},
    "ET": {"name": "Ethiopia", "currency": "ETB", "wb_code": "ETH"},
    "BI": {"name": "Burundi", "currency": "BIF", "wb_code": "BDI"},
    "SS": {"name": "South Sudan", "currency": "SSP", "wb_code": "SSD"},
    "CD": {"name": "DR Congo", "currency": "CDF", "wb_code": "COD"},
    "SO": {"name": "Somalia", "currency": "SOS", "wb_code": "SOM"},
}

# ── World Bank Indicators ───────────────────────────────────────────────────────
WB_INDICATORS = {
    "inflation": "FP.CPI.TOTL.ZG",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "unemployment": "SL.UEM.TOTL.ZS",
    "fuel_imports": "TM.VAL.FUEL.ZS.UN",
    "current_account": "BN.CAB.XOKA.GD.ZS",
    "external_debt": "DT.DOD.DECT.GN.ZS",
    "interest_rate": "FR.INR.LEND",
}

config = Config()
