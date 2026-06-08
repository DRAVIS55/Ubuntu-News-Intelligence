"""
intelligence/patterns.py — Layer 2: Trend and Pattern Detection
Automatically surfaces patterns across multiple articles that no single journalist would see.
Updated to use Django ORM instead of SQLAlchemy.
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.config import config
from core.models import Article, DetectedPattern, PatternMember
from intelligence.llm import get_llm

logger = logging.getLogger(__name__)


# ── Pattern Detection Strategies ───────────────────────────────────────────────

def detect_entity_clusters(days: int = 30, min_occurrences: int = 3) -> list[dict]:
    """
    Find entities (people, orgs) appearing frequently in suspicious contexts.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = (
        Article.objects
        .filter(published_at__gte=cutoff)
        .exclude(entity_tags__isnull=True)
    )

    entity_category_counts = defaultdict(list)
    for article in recent:
        tags = article.entity_tags or {}
        text = (article.title + " " + article.body[:500]).lower()
        if any(word in text for word in [
            "corruption", "fraud", "investigation", "arrested", "charged",
            "tender", "procurement", "scandal", "probe"
        ]):
            for org in tags.get("organisations", [])[:5]:
                entity_category_counts[f"ORG:{org}"].append(article.id)
            for person in tags.get("persons", [])[:5]:
                entity_category_counts[f"PERSON:{person}"].append(article.id)

    patterns = []
    for entity_key, article_ids in entity_category_counts.items():
        if len(article_ids) >= min_occurrences:
            entity_type, entity_name = entity_key.split(":", 1)
            patterns.append({
                "type": "entity_cluster",
                "entity": entity_name,
                "entity_type": entity_type,
                "article_ids": list(set(article_ids)),
                "occurrence_count": len(set(article_ids)),
                "title": f"{entity_name} appears in {len(set(article_ids))} accountability stories",
                "severity": "high" if len(set(article_ids)) >= 5 else "medium",
            })

    return patterns


def detect_topic_spikes(days: int = 7, baseline_days: int = 30) -> list[dict]:
    """
    Detect topics that are suddenly appearing more than usual.
    """
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(days=days)
    baseline_cutoff = now - timedelta(days=baseline_days)

    recent_articles = list(Article.objects.filter(published_at__gte=recent_cutoff))
    baseline_articles = list(
        Article.objects.filter(published_at__gte=baseline_cutoff, published_at__lt=recent_cutoff)
    )

    spike_keywords = [
        "strike", "protests", "drought", "flood", "fuel shortage", "power cut",
        "electricity", "water shortage", "food prices", "arrest", "murder",
        "accident", "fire", "election", "petition", "court", "parliament",
    ]

    def count_keyword_hits(articles, keywords):
        counts = Counter()
        for art in articles:
            text = (art.title + " " + art.body[:500]).lower()
            for kw in keywords:
                if kw in text:
                    counts[kw] += 1
        return counts

    recent_counts = count_keyword_hits(recent_articles, spike_keywords)
    baseline_counts = count_keyword_hits(baseline_articles, spike_keywords)

    recent_norm = {k: v / days for k, v in recent_counts.items()}
    baseline_norm = {k: v / (baseline_days - days) for k, v in baseline_counts.items()}

    patterns = []
    for kw in spike_keywords:
        recent_rate = recent_norm.get(kw, 0)
        baseline_rate = baseline_norm.get(kw, 0.01)
        spike_ratio = recent_rate / baseline_rate

        if spike_ratio >= 2.5 and recent_counts.get(kw, 0) >= 3:
            matching_ids = [
                art.id for art in recent_articles
                if kw in (art.title + " " + art.body[:200]).lower()
            ]
            patterns.append({
                "type": "topic_spike",
                "keyword": kw,
                "spike_ratio": round(spike_ratio, 1),
                "recent_count": recent_counts.get(kw, 0),
                "article_ids": matching_ids[:20],
                "title": f"'{kw}' coverage up {spike_ratio:.1f}x in past {days} days",
                "severity": "high" if spike_ratio >= 5 else "medium",
            })

    return patterns


def detect_geographic_clustering(days: int = 14) -> list[dict]:
    """
    Detect when multiple stories are hitting the same region simultaneously.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = list(Article.objects.filter(published_at__gte=cutoff).exclude(country_code__isnull=True))

    country_counts = Counter(a.country_code for a in recent if a.country_code)
    total = len(recent)

    patterns = []
    for country, count in country_counts.most_common(5):
        proportion = count / total if total > 0 else 0
        if proportion > 0.4 and count > 20:
            patterns.append({
                "type": "geographic_concentration",
                "country_code": country,
                "article_count": count,
                "proportion_pct": round(proportion * 100, 1),
                "article_ids": [a.id for a in recent if a.country_code == country][:20],
                "title": f"{country} accounts for {proportion*100:.0f}% of regional coverage",
                "severity": "medium",
            })

    return patterns


def detect_election_cycle_patterns(days: int = 60) -> list[dict]:
    """
    Detect election-related patterns that historically precede unrest.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    election_terms = [
        "election", "vote", "ballot", "IEBC", "candidate", "campaign",
        "polling", "constituency", "MP", "governor", "senator"
    ]

    recent = list(Article.objects.filter(published_at__gte=cutoff))

    election_articles = []
    for art in recent:
        text = (art.title + " " + art.body[:500]).lower()
        if sum(1 for term in election_terms if term.lower() in text) >= 2:
            election_articles.append(art)

    if len(election_articles) < 10:
        return []

    violence_terms = ["violence", "clashes", "killed", "deaths", "teargas", "protest"]
    election_violence = [
        art for art in election_articles
        if any(t in (art.title + " " + art.body[:500]).lower() for t in violence_terms)
    ]

    patterns = []
    if len(election_violence) >= 3:
        patterns.append({
            "type": "election_violence_pattern",
            "article_ids": [a.id for a in election_violence],
            "occurrence_count": len(election_violence),
            "title": f"Election-related violence coverage: {len(election_violence)} articles in {days} days",
            "severity": "high",
        })

    return patterns


# ── Pattern Persistence ─────────────────────────────────────────────────────────

def save_pattern(pattern_data: dict) -> Optional[DetectedPattern]:
    """
    Save a detected pattern to the database. Deduplicates by title.
    """
    existing = DetectedPattern.objects.filter(
        title=pattern_data["title"], is_active=True
    ).first()

    if existing:
        existing.last_seen = datetime.now(timezone.utc)
        existing.article_count = pattern_data.get("occurrence_count", existing.article_count)
        existing.save()
        return existing

    pattern = DetectedPattern.objects.create(
        pattern_type=pattern_data["type"],
        title=pattern_data["title"],
        description=pattern_data.get("description", ""),
        severity=pattern_data.get("severity", "medium"),
        first_seen=datetime.now(timezone.utc),
        article_count=pattern_data.get("occurrence_count", len(pattern_data.get("article_ids", []))),
        country_codes=pattern_data.get("country_codes", []),
        meta=pattern_data,
    )

    for article_id in pattern_data.get("article_ids", [])[:50]:
        try:
            article = Article.objects.get(id=article_id)
            PatternMember.objects.create(
                pattern=pattern,
                article=article,
                relevance_score=1.0,
            )
        except Article.DoesNotExist:
            pass

    return pattern


def run_pattern_detection() -> int:
    """
    Run all pattern detectors and persist results.
    Returns number of new patterns detected.
    """
    all_patterns = []
    all_patterns.extend(detect_entity_clusters(
        days=config.PATTERN_DETECTION_WINDOW_DAYS,
        min_occurrences=config.PATTERN_MIN_OCCURRENCES
    ))
    all_patterns.extend(detect_topic_spikes())
    all_patterns.extend(detect_geographic_clustering())
    all_patterns.extend(detect_election_cycle_patterns())

    new_count = 0
    for p in all_patterns:
        saved = save_pattern(p)
        if saved:
            new_count += 1

    logger.info(f"Pattern detection: {len(all_patterns)} patterns processed, {new_count} updated/created")
    return new_count


def generate_pattern_summary(pattern: DetectedPattern) -> str:
    """
    Generate an editorial summary for a detected pattern using LLM.
    """
    llm = get_llm()

    prompt = f"""You are a senior investigative editor. A pattern detection system has flagged the following:

Pattern Type: {pattern.pattern_type}
Title: {pattern.title}
Severity: {pattern.severity}
Article Count: {pattern.article_count}
Detected: {pattern.first_seen}
Metadata: {pattern.meta}

In 2-3 sentences, explain what this pattern means for a journalist and why it matters.
What story might be hiding here? What should a journalist investigate?"""

    return llm.complete(prompt, max_tokens=300, temperature=0.4)
