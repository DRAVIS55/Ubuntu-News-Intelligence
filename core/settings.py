"""
core/settings.py — Django settings for the African News Intelligence Platform
Replaces Flask app config; used by manage.py and run.py
"""

import os
import dj_database_url
from pathlib import Path
from core.config import config

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Core ───────────────────────────────────────────────────────────────────────
SECRET_KEY = config.SECRET_KEY
DEBUG = config.DEBUG
ALLOWED_HOSTS = config.ALLOWED_HOSTS

# ── Applications ───────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    # Platform apps
    "core",
    "api",
    "dashboard",
    "ingestion",
    "intelligence",
]

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# ── URL routing ────────────────────────────────────────────────────────────────
ROOT_URLCONF = "core.urls"

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "dashboard" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

# ── Database ───────────────────────────────────────────────────────────────────
# Support both postgresql:// and sqlite:// DATABASE_URL
_db_url = config.DATABASE_URL
if _db_url.startswith("sqlite"):
    # Convert sqlite:///path to Django format
    _sqlite_path = _db_url.replace("sqlite:///", "")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / _sqlite_path,
        }
    }
else:
    try:
        import dj_database_url as _dj
        DATABASES = {"default": _dj.parse(_db_url)}
    except ImportError:
        # Manual parse for postgresql://user:pass@host:port/dbname
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": _db_url.split("/")[-1],
                "USER": _db_url.split("://")[1].split(":")[0],
                "PASSWORD": _db_url.split(":")[2].split("@")[0],
                "HOST": _db_url.split("@")[1].split(":")[0],
                "PORT": _db_url.split("@")[1].split(":")[1].split("/")[0],
            }
        }

# ── Static files ───────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "dashboard" / "static"]

# ── Django REST Framework ──────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
    },
    "EXCEPTION_HANDLER": "api.views.custom_exception_handler",
}

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Restrict in production via CORS_ALLOWED_ORIGINS
CORS_URLS_REGEX = r"^/api/.*$"

# ── Internationalisation ───────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = False
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
