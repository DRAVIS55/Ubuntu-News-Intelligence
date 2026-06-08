"""
scripts/init_db.py — Initialise the database schema for Django
Run once before starting the platform for the first time.
Django handles relational DB migrations; this script initialises ChromaDB.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

import logging
from rich.console import Console
from rich.panel import Panel
from django.core.management import call_command

console = Console()
logging.basicConfig(level=logging.WARNING)


def init():
    console.print(Panel.fit(
        "[bold green]African News Intelligence Platform[/bold green]\n"
        "[dim]Database Initialisation — Django[/dim]",
        border_style="green"
    ))

    # ── Django Migrations ──────────────────────────────────────────────────
    console.print("\n[bold]1. Running Django migrations...[/bold]")
    try:
        call_command("migrate", "--run-syncdb", verbosity=0)
        console.print("   [green]✓[/green] Django ORM tables created / migrated")
    except Exception as e:
        console.print(f"   [red]✗[/red] Migration failed: {e}")
        sys.exit(1)

    # ── ChromaDB ──────────────────────────────────────────────────────────
    console.print("\n[bold]2. Initialising vector database (ChromaDB)...[/bold]")
    from core.database import get_articles_collection, health_check_chroma
    get_articles_collection()
    ok = health_check_chroma()
    if ok:
        console.print("   [green]✓[/green] ChromaDB collection ready")
    else:
        console.print("   [red]✗[/red] ChromaDB init failed")
        sys.exit(1)

    # ── DB health check ───────────────────────────────────────────────────
    console.print("\n[bold]3. Verifying database connection...[/bold]")
    from core.database import health_check_db
    ok = health_check_db()
    if ok:
        console.print("   [green]✓[/green] Database reachable")
    else:
        console.print("   [red]✗[/red] Database connection failed — check DATABASE_URL in .env")
        sys.exit(1)

    # ── Data directories ──────────────────────────────────────────────────
    console.print("\n[bold]4. Creating data directories...[/bold]")
    dirs = ["data/chroma_db", "data/logs", "data/sample", "models"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        console.print(f"   [green]✓[/green] {d}/")

    console.print(Panel.fit(
        "[bold green]✓ Initialisation complete![/bold green]\n\n"
        "Next steps:\n"
        "  1. [cyan]python scripts/seed_data.py[/cyan]   — load sample articles\n"
        "  2. [cyan]python run.py[/cyan]                 — start the platform\n"
        "  3. Open [link=http://localhost:8000]http://localhost:8000[/link]",
        border_style="green"
    ))


if __name__ == "__main__":
    init()
