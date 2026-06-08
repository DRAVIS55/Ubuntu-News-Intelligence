"""
api/views.py — REST API views for the African News Intelligence Platform
All features accessible via JSON API for CMS integration.
Built with Django REST Framework replacing Flask blueprints.
"""

import logging
from datetime import datetime, timezone
from functools import wraps

from django.http import JsonResponse
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler

from core.config import config
from core.models import Article, DetectedPattern, IngestionLog
from ingestion.embedder import semantic_search
from ingestion.scheduler import trigger_now
from intelligence.rag import (
    generate_headlines,
    get_context_brief,
    generate_research_brief,
    rewrite_article,
    fact_check_article,
)
from intelligence.comparisons import generate_comparison_report, get_fuel_comparison
from intelligence.relations import get_article_parallels
from intelligence.patterns import generate_pattern_summary

logger = logging.getLogger(__name__)


# ── Custom exception handler ───────────────────────────────────────────────────

def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {"success": False, "error": response.data}
    return response


# ── Auth decorator ─────────────────────────────────────────────────────────────

def require_admin_token(view_func):
    """Simple admin token check for protected endpoints."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        key = (
            request.headers.get("X-Admin-Token")
            or request.GET.get("admin_token")
        )
        if key != config.ADMIN_TOKEN:
            return Response({"success": False, "error": "Unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def api_ok(data, status_code=200):
    return Response({"success": True, "data": data}, status=status_code)


def api_err(error, status_code=400):
    return Response({"success": False, "error": error}, status=status_code)


# ── Health ──────────────────────────────────────────────────────────────────────

@api_view(["GET"])
def health(request):
    from core.database import health_check_db, health_check_chroma
    return api_ok({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db": health_check_db(),
        "vector_db": health_check_chroma(),
        "llm_provider": config.LLM_PROVIDER,
        "framework": "django",
    })


# ── Archive Search ──────────────────────────────────────────────────────────────

@api_view(["GET"])
def search(request):
    """
    Semantic search over the article archive.

    Query params:
        q: Search query (required)
        n: Number of results (default 10, max 50)
        country: ISO-2 country code filter (e.g. KE)
        category: Category filter (e.g. business)
    """
    query = request.GET.get("q", "").strip()
    if not query:
        return api_err("Query parameter 'q' is required")

    n = min(int(request.GET.get("n", 10)), 50)
    country = request.GET.get("country")
    category = request.GET.get("category")

    results = semantic_search(query, n_results=n, country_code=country, category=category)
    return api_ok({"query": query, "results": results, "count": len(results)})


# ── Article Tools ───────────────────────────────────────────────────────────────

@api_view(["POST"])
def headlines(request):
    """
    Generate headline options for an article.
    Body: {"text": "article body...", "n": 5}
    """
    data = request.data
    if not data or not data.get("text"):
        return api_err("Request body must include 'text'")

    article_text = data["text"][:10000]
    n = min(int(data.get("n", 5)), 10)

    results = generate_headlines(article_text, n=n)
    return api_ok({"headlines": results, "count": len(results)})


@api_view(["POST"])
def context_brief(request):
    """
    Generate historical context brief for an article.
    Body: {"text": "...", "title": "..."}
    """
    data = request.data
    if not data or not data.get("text"):
        return api_err("Request body must include 'text'")

    result = get_context_brief(
        article_text=data["text"][:8000],
        article_title=data.get("title", ""),
    )
    return api_ok(result)


@api_view(["POST"])
def rewrite(request):
    """
    Improve a draft article.
    Body: {"text": "...", "style": "standard|concise|investigative"}
    """
    data = request.data
    if not data or not data.get("text"):
        return api_err("Request body must include 'text'")

    style = data.get("style", "standard")
    if style not in ("standard", "concise", "investigative"):
        style = "standard"

    result = rewrite_article(article_text=data["text"][:8000], style=style)
    return api_ok(result)


@api_view(["POST"])
def factcheck(request):
    """
    Fact-check an article against the archive.
    Body: {"text": "..."}
    """
    data = request.data
    if not data or not data.get("text"):
        return api_err("Request body must include 'text'")

    result = fact_check_article(article_text=data["text"][:6000])
    return api_ok(result)


@api_view(["POST"])
def research_brief(request):
    """
    Generate a research brief on a topic.
    Body: {"topic": "...", "country_code": "KE"}
    """
    data = request.data
    if not data or not data.get("topic"):
        return api_err("Request body must include 'topic'")

    topic = data["topic"][:500]
    country_code = data.get("country_code", "KE")

    result = generate_research_brief(topic=topic, country_code=country_code)
    return api_ok(result)


@api_view(["GET"])
def article_parallels(request, article_id):
    """
    Get historical parallels for a specific article.
    Query params: min_similarity (default 0.6)
    """
    min_sim = float(request.GET.get("min_similarity", 0.6))
    results = get_article_parallels(article_id, min_similarity=min_sim)
    return api_ok({"article_id": article_id, "parallels": results, "count": len(results)})


@api_view(["GET"])
def get_article(request, article_id):
    """Get a single article by ID."""
    try:
        article = Article.objects.get(id=article_id)
        return api_ok(article.to_dict())
    except Article.DoesNotExist:
        return api_err("Article not found", status_code=404)


@api_view(["GET"])
def list_articles(request):
    """
    List recent articles.
    Query params: country, category, limit (default 20, max 100), offset
    """
    country = request.GET.get("country")
    category = request.GET.get("category")
    limit = min(int(request.GET.get("limit", 20)), 100)
    offset = int(request.GET.get("offset", 0))

    qs = Article.objects.all().order_by("-published_at")
    if country:
        qs = qs.filter(country_code=country)
    if category:
        qs = qs.filter(category=category)

    total = qs.count()
    articles = qs[offset: offset + limit]

    return api_ok({
        "articles": [a.to_dict() for a in articles],
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── Intelligence Endpoints ──────────────────────────────────────────────────────

@api_view(["POST"])
def compare(request):
    """
    Generate an EAC peer comparison for an article.
    Body: {"text": "...", "country_code": "KE"}
    """
    data = request.data
    if not data or not data.get("text"):
        return api_err("Request body must include 'text'")

    result = generate_comparison_report(
        article_text=data["text"][:5000],
        focus_country=data.get("country_code", "KE"),
    )
    return api_ok(result)


@api_view(["GET"])
def fuel_comparison(request):
    """Return current fuel price comparison across EAC countries."""
    result = get_fuel_comparison()
    return api_ok(result)


@api_view(["GET"])
def patterns(request):
    """
    List detected patterns.
    Query params: severity (low|medium|high), active (default true), limit (default 20)
    """
    severity = request.GET.get("severity")
    active = request.GET.get("active", "true").lower() == "true"
    limit = min(int(request.GET.get("limit", 20)), 100)

    qs = DetectedPattern.objects.filter(is_active=active).order_by("-last_seen")
    if severity:
        qs = qs.filter(severity=severity)

    result = qs[:limit]
    return api_ok({
        "patterns": [p.to_dict() for p in result],
        "count": len(result),
    })


@api_view(["GET"])
def pattern_detail(request, pattern_id):
    """Get a specific pattern with its LLM-generated summary."""
    try:
        pattern = DetectedPattern.objects.get(id=pattern_id)
    except DetectedPattern.DoesNotExist:
        return api_err("Pattern not found", status_code=404)

    data = pattern.to_dict()
    try:
        data["summary"] = generate_pattern_summary(pattern)
    except Exception as e:
        logger.warning(f"Could not generate pattern summary: {e}")
        data["summary"] = None

    return api_ok(data)


@api_view(["GET"])
def daily_briefing(request):
    """
    Generate a daily news briefing.
    Query params: country_code (default KE)
    """
    country_code = request.GET.get("country_code", "KE")

    # Get today's top articles
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_articles = list(
        Article.objects
        .filter(published_at__gte=cutoff, country_code=country_code)
        .order_by("-published_at")[:10]
    )

    if not recent_articles:
        recent_articles = list(
            Article.objects
            .filter(country_code=country_code)
            .order_by("-published_at")[:10]
        )

    article_summaries = "\n\n".join([
        f"- {a.title} ({a.source_name}, {a.published_at.strftime('%d %b') if a.published_at else '?'})"
        for a in recent_articles
    ])

    from intelligence.llm import get_llm
    llm = get_llm()
    briefing_prompt = f"""You are a senior editor compiling a daily news briefing for {country_code}.

Today's top stories:
{article_summaries}

Write a concise 3-4 paragraph daily briefing that:
1. Leads with the most significant story and why it matters
2. Identifies common themes across stories
3. Notes any developing situations to watch
4. Provides regional context where relevant

Be specific, factual, and useful for a journalist starting their day."""

    try:
        briefing_text = llm.complete(briefing_prompt, max_tokens=800, temperature=0.3)
    except Exception as e:
        briefing_text = f"Could not generate briefing: {e}"

    return api_ok({
        "country_code": country_code,
        "briefing": briefing_text,
        "article_count": len(recent_articles),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })


# ── Admin Endpoints ─────────────────────────────────────────────────────────────

@api_view(["POST"])
@require_admin_token
def admin_ingest(request):
    """Trigger an immediate ingestion run."""
    trigger_now()
    return api_ok({"message": "Ingestion pipeline triggered"})


@api_view(["GET"])
@require_admin_token
def admin_stats(request):
    """Platform statistics."""
    from core.database import health_check_chroma, get_articles_collection

    article_count = Article.objects.count()
    pattern_count = DetectedPattern.objects.filter(is_active=True).count()
    last_log = IngestionLog.objects.order_by("-started_at").first()

    vector_count = 0
    try:
        col = get_articles_collection()
        vector_count = col.count()
    except Exception:
        pass

    return api_ok({
        "articles": article_count,
        "vectors": vector_count,
        "active_patterns": pattern_count,
        "llm_provider": config.LLM_PROVIDER,
        "last_ingestion": last_log.to_dict() if last_log else None,
    })


@api_view(["GET"])
@require_admin_token
def admin_logs(request):
    """Recent ingestion logs."""
    limit = min(int(request.GET.get("limit", 10)), 50)
    logs = IngestionLog.objects.order_by("-started_at")[:limit]
    return api_ok({"logs": [log.to_dict() for log in logs]})
