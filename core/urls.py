"""
core/urls.py — Root URL configuration
Routes API requests and serves the dashboard SPA
"""

from django.urls import path, include
from dashboard.views import dashboard_view

urlpatterns = [
    # REST API — all routes under /api/v1/
    path("api/v1/", include("api.urls")),

    # Dashboard SPA — catch-all (must be last)
    path("", dashboard_view),
    path("<path:path>", dashboard_view),
]
