"""
tests/test_platform.py — Test suite for the African News Intelligence Platform
Run: pytest tests/ -v

Updated to use pytest-django instead of Flask test client.
"""

import pytest
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Django test settings ────────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ["DATABASE_URL"] = "sqlite:///test_anip.db"
os.environ["CHROMA_PATH"] = "./test_chroma"
os.environ["LLM_PROVIDER"] = "anthropic"  # will be mocked
os.environ["SECRET_KEY"] = "test-secret-key"


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def django_db_setup(django_test_environment):
    """Django handles DB setup via pytest-django."""
    pass


@pytest.fixture
def sample_article_data():
    return {
        "source_name": "Test Nation",
        "source_url": "https://test.example.com/article/1",
        "title": "CBK raises interest rates to 13% amid inflation concerns",
        "body": "The Central Bank of Kenya has raised its benchmark lending rate by 50 basis points to 13 percent. The Monetary Policy Committee cited persistent inflation above the 7.5 percent upper target band.",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=2),
        "country_code": "KE",
        "category": "business",
        "language": "en",
        "chroma_id": "test-cbk-rate-2024-django",
    }


@pytest.fixture
def api_client():
    from django.test import Client
    return Client()


# ── Model Tests ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestArticleModel:
    def test_article_to_dict(self, sample_article_data):
        from core.models import Article
        article = Article(**sample_article_data)
        d = article.to_dict()
        assert d["title"] == sample_article_data["title"]
        assert d["country_code"] == "KE"
        assert d["category"] == "business"
        assert "body" not in d

    def test_article_str(self, sample_article_data):
        from core.models import Article
        article = Article(**sample_article_data)
        r = str(article)
        assert "CBK raises" in r


# ── Scraper Tests ───────────────────────────────────────────────────────────────

class TestScraper:
    def test_make_chroma_id(self):
        from ingestion.scraper import _make_chroma_id
        id1 = _make_chroma_id("https://example.com/article", "Test title")
        id2 = _make_chroma_id("https://example.com/article", "Test title")
        id3 = _make_chroma_id("https://example.com/article", "Different title")
        assert id1 == id2
        assert id1 != id3
        assert len(id1) == 40

    def test_clean_html(self):
        from ingestion.scraper import _clean_html
        raw = "<p>Hello <strong>world</strong></p><div>  More   text  </div>"
        result = _clean_html(raw)
        assert "Hello world" in result
        assert "<p>" not in result

    def test_count_words(self):
        from ingestion.scraper import _count_words
        assert _count_words("hello world test") == 3

    @pytest.mark.django_db
    def test_store_articles_deduplication(self, sample_article_data):
        from ingestion.scraper import store_articles

        articles = [sample_article_data.copy()]
        articles[0]["chroma_id"] = "unique-dedup-django-test-456"

        stored1, skipped1 = store_articles(articles)
        stored2, skipped2 = store_articles(articles)

        assert stored1 == 1
        assert stored2 == 0
        assert skipped2 == 1


# ── Config Tests ────────────────────────────────────────────────────────────────

class TestConfig:
    def test_config_loads(self):
        from core.config import config
        assert config.LLM_PROVIDER in ("anthropic", "openai", "local")
        assert config.PORT > 0
        assert config.EMBEDDING_MODEL

    def test_news_sources_structure(self):
        from core.config import NEWS_SOURCES
        assert len(NEWS_SOURCES) > 0
        for source in NEWS_SOURCES:
            assert "name" in source
            assert "url" in source
            assert "country" in source

    def test_eac_countries(self):
        from core.config import EAC_COUNTRIES
        assert "KE" in EAC_COUNTRIES
        assert "TZ" in EAC_COUNTRIES
        assert EAC_COUNTRIES["KE"]["name"] == "Kenya"

    def test_wb_indicators(self):
        from core.config import WB_INDICATORS
        assert "inflation" in WB_INDICATORS
        assert "gdp_growth" in WB_INDICATORS

    def test_django_settings(self):
        from django.conf import settings
        assert settings.SECRET_KEY
        assert "rest_framework" in settings.INSTALLED_APPS
        assert "corsheaders" in settings.INSTALLED_APPS


# ── API Tests ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAPIRoutes:
    def test_health_endpoint(self, api_client):
        resp = api_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert "status" in data["data"]
        assert data["data"]["framework"] == "django"

    def test_search_requires_query(self, api_client):
        resp = api_client.get("/api/v1/search")
        assert resp.status_code == 400

    def test_search_returns_results_structure(self, api_client):
        resp = api_client.get("/api/v1/search?q=Kenya+fuel+prices")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert "results" in data["data"]
        assert "count" in data["data"]

    def test_headlines_requires_text(self, api_client):
        resp = api_client.post(
            "/api/v1/articles/headlines",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_articles_list(self, api_client):
        resp = api_client.get("/api/v1/articles?limit=5")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert "articles" in data["data"]
        assert "total" in data["data"]

    def test_articles_list_country_filter(self, api_client):
        resp = api_client.get("/api/v1/articles?country=KE&limit=5")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True

    def test_fuel_comparison(self, api_client):
        resp = api_client.get("/api/v1/compare/fuel")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert "comparison" in data["data"]
        assert len(data["data"]["comparison"]) > 0

    def test_patterns_endpoint(self, api_client):
        resp = api_client.get("/api/v1/patterns")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["success"] is True
        assert "patterns" in data["data"]

    def test_admin_requires_token(self, api_client):
        resp = api_client.post("/api/v1/admin/ingest")
        assert resp.status_code == 401

    def test_admin_stats_with_token(self, api_client):
        resp = api_client.get(
            "/api/v1/admin/stats",
            HTTP_X_ADMIN_TOKEN=os.environ.get("ADMIN_TOKEN", "dev-admin-token"),
        )
        assert resp.status_code == 200

    def test_article_not_found(self, api_client):
        resp = api_client.get("/api/v1/articles/999999")
        assert resp.status_code == 404

    def test_dashboard_loads(self, api_client):
        resp = api_client.get("/")
        assert resp.status_code == 200
        assert b"African News Intelligence" in resp.content


# ── Comparison Engine Tests ─────────────────────────────────────────────────────

class TestComparisons:
    def test_fuel_comparison_structure(self):
        from intelligence.comparisons import get_fuel_comparison
        result = get_fuel_comparison()
        assert "comparison" in result
        assert "eac_average_usd" in result
        assert "kenya_vs_eac_average_pct" in result
        assert len(result["comparison"]) >= 3

    def test_fuel_comparison_has_kenya(self):
        from intelligence.comparisons import get_fuel_comparison
        result = get_fuel_comparison()
        countries = [c["country_code"] for c in result["comparison"]]
        assert "KE" in countries

    def test_fuel_prices_in_usd(self):
        from intelligence.comparisons import get_fuel_comparison
        result = get_fuel_comparison()
        for item in result["comparison"]:
            assert item["petrol_usd_per_litre"] > 0
            assert item["petrol_usd_per_litre"] < 10


# ── Pattern Detection Tests ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPatterns:
    def test_entity_cluster_detection(self):
        from intelligence.patterns import detect_entity_clusters
        result = detect_entity_clusters(days=30, min_occurrences=2)
        assert isinstance(result, list)
        for p in result:
            assert "type" in p
            assert "title" in p
            assert "severity" in p

    def test_topic_spike_detection(self):
        from intelligence.patterns import detect_topic_spikes
        result = detect_topic_spikes(days=7)
        assert isinstance(result, list)

    def test_geographic_clustering(self):
        from intelligence.patterns import detect_geographic_clustering
        result = detect_geographic_clustering()
        assert isinstance(result, list)


# ── Entity Extraction Tests ─────────────────────────────────────────────────────

class TestEntityExtraction:
    def test_extract_entities_returns_dict(self):
        from intelligence.relations import extract_entities, get_nlp
        if get_nlp() is None:
            pytest.skip("spaCy model not installed")

        text = "President William Ruto met with CBK Governor Kamau Thugge in Nairobi."
        result = extract_entities(text)
        assert isinstance(result, dict)
        assert "persons" in result
        assert "organisations" in result
        assert "places" in result

    def test_extract_entities_finds_nairobi(self):
        from intelligence.relations import extract_entities, get_nlp
        if get_nlp() is None:
            pytest.skip("spaCy model not installed")

        text = "The meeting took place in Nairobi, Kenya's capital city."
        result = extract_entities(text)
        places = result.get("places", [])
        assert any("Nairobi" in p for p in places)


# ── Embedder Tests ──────────────────────────────────────────────────────────────

class TestEmbedder:
    def test_embed_text_returns_list(self):
        from ingestion.embedder import embed_text
        result = embed_text("Kenya raises fuel prices amid inflation")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, float) for x in result)

    def test_embed_text_is_normalised(self):
        import math
        from ingestion.embedder import embed_text
        result = embed_text("Test sentence")
        magnitude = math.sqrt(sum(x ** 2 for x in result))
        assert abs(magnitude - 1.0) < 0.01

    def test_semantic_search_returns_list(self):
        from ingestion.embedder import semantic_search
        result = semantic_search("Kenya interest rates")
        assert isinstance(result, list)

    def test_semantic_search_structure(self):
        from ingestion.embedder import semantic_search
        results = semantic_search("Tanzania economy", n_results=3)
        for r in results:
            assert "rank" in r
            assert "similarity" in r
            assert "title" in r
            assert 0 <= r["similarity"] <= 1


# ── Integration Test ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIntegration:
    def test_article_ingestion_to_search_pipeline(self):
        """End-to-end: store article → embed → search and find it."""
        from ingestion.scraper import store_articles
        from ingestion.embedder import embed_articles, semantic_search

        unique_title = "Django Integration Test Article on Nairobi Water Crisis 2024"
        unique_id = hashlib.sha256(unique_title.encode()).hexdigest()[:40]

        article_data = [{
            "source_name": "Test Source",
            "source_url": "https://test.example.com/django-integration-test",
            "title": unique_title,
            "body": "The Nairobi City Water and Sewerage Company has declared a water shortage affecting 2 million residents. The shortage follows a burst main water pipe at Ruiru treatment plant.",
            "published_at": datetime.now(timezone.utc),
            "country_code": "KE",
            "category": "health",
            "language": "en",
            "chroma_id": unique_id,
        }]

        stored, _ = store_articles(article_data)
        assert stored == 1

        embedded = embed_articles()
        assert embedded >= 1

        results = semantic_search("Nairobi water shortage burst pipe")
        assert len(results) > 0
        titles = [r["title"] for r in results]
        assert any("Nairobi" in t or "Water" in t for t in titles)
