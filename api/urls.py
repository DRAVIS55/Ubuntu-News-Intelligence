"""
api/urls.py — URL patterns for the REST API
All routes are prefixed with /api/v1/ by core/urls.py
"""

from django.urls import path
from api import views

urlpatterns = [
    # Health
    path("health", views.health, name="health"),

    # Archive Search
    path("search", views.search, name="search"),

    # Article Tools
    path("articles/headlines", views.headlines, name="headlines"),
    path("articles/context", views.context_brief, name="context_brief"),
    path("articles/rewrite", views.rewrite, name="rewrite"),
    path("articles/factcheck", views.factcheck, name="factcheck"),
    path("articles/research", views.research_brief, name="research_brief"),
    path("articles/<int:article_id>/parallels", views.article_parallels, name="article_parallels"),
    path("articles/<int:article_id>", views.get_article, name="get_article"),
    path("articles", views.list_articles, name="list_articles"),

    # Intelligence
    path("compare/eac", views.compare, name="compare"),
    path("compare/fuel", views.fuel_comparison, name="fuel_comparison"),
    path("patterns", views.patterns, name="patterns"),
    path("patterns/<int:pattern_id>", views.pattern_detail, name="pattern_detail"),
    path("briefing", views.daily_briefing, name="daily_briefing"),

    # Admin
    path("admin/ingest", views.admin_ingest, name="admin_ingest"),
    path("admin/stats", views.admin_stats, name="admin_stats"),
    path("admin/logs", views.admin_logs, name="admin_logs"),
]
