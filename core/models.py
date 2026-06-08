"""
core/models.py — Django ORM models for the platform
Replaces SQLAlchemy models; Django manages migrations automatically.
"""

from django.db import models


class Article(models.Model):
    """A news article ingested from any source."""

    source_name = models.CharField(max_length=200)
    source_url = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    body = models.TextField()
    summary = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=200, blank=True, null=True)
    published_at = models.DateTimeField()
    ingested_at = models.DateTimeField(auto_now_add=True)
    country_code = models.CharField(max_length=5, blank=True, null=True)   # KE, TZ, UG, etc.
    category = models.CharField(max_length=100, blank=True, null=True)    # politics, business, etc.
    language = models.CharField(max_length=10, default="en")
    chroma_id = models.CharField(max_length=100, unique=True)              # vector DB reference
    entity_tags = models.JSONField(null=True, blank=True)                  # extracted entities
    topic_tags = models.JSONField(null=True, blank=True)                   # detected topics
    is_processed = models.BooleanField(default=False)
    word_count = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "articles"
        indexes = [
            models.Index(fields=["published_at"]),
            models.Index(fields=["country_code"]),
            models.Index(fields=["category"]),
        ]

    def to_dict(self):
        return {
            "id": self.id,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "title": self.title,
            "summary": self.summary,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "country_code": self.country_code,
            "category": self.category,
            "language": self.language,
            "entity_tags": self.entity_tags,
            "topic_tags": self.topic_tags,
            "word_count": self.word_count,
        }

    def __str__(self):
        return f"<Article {self.id}: {self.title[:60]}>"


class ArticleRelation(models.Model):
    """A semantic relationship between two articles (past-present linking)."""

    source = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="relations_as_source"
    )
    target = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="relations_as_target"
    )
    similarity_score = models.FloatField()          # 0.0 – 1.0
    relation_type = models.CharField(max_length=50, blank=True, null=True)
    context_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "article_relations"
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["similarity_score"]),
        ]

    def to_dict(self):
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "similarity_score": self.similarity_score,
            "relation_type": self.relation_type,
            "context_note": self.context_note,
        }


class DetectedPattern(models.Model):
    """A trend or anomaly detected across multiple articles."""

    SEVERITY_CHOICES = [("low", "Low"), ("medium", "Medium"), ("high", "High")]

    pattern_type = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    first_seen = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    article_count = models.IntegerField(default=0)
    country_codes = models.JSONField(null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)   # renamed from 'metadata' (reserved word)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "detected_patterns"

    def to_dict(self):
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "article_count": self.article_count,
            "country_codes": self.country_codes,
        }


class PatternMember(models.Model):
    """Links an article to a detected pattern."""

    pattern = models.ForeignKey(
        DetectedPattern, on_delete=models.CASCADE, related_name="members"
    )
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="patterns"
    )
    relevance_score = models.FloatField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pattern_members"


class CountryMetric(models.Model):
    """Cached economic metrics from World Bank / IMF for peer comparison."""

    country_code = models.CharField(max_length=5)
    indicator_code = models.CharField(max_length=50)
    indicator_name = models.CharField(max_length=200, blank=True, null=True)
    value = models.FloatField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "country_metrics"
        indexes = [
            models.Index(fields=["country_code", "indicator_code"]),
        ]

    def to_dict(self):
        return {
            "country_code": self.country_code,
            "indicator_code": self.indicator_code,
            "indicator_name": self.indicator_name,
            "value": self.value,
            "year": self.year,
        }


class ShengEntry(models.Model):
    """Sheng lexicon entry — maps Sheng terms to Swahili/English equivalents."""

    sheng_term = models.CharField(max_length=100, unique=True)
    swahili_equivalent = models.CharField(max_length=200, blank=True, null=True)
    english_equivalent = models.CharField(max_length=200, blank=True, null=True)
    usage_examples = models.JSONField(null=True, blank=True)
    frequency = models.IntegerField(default=1)
    contributed_by = models.CharField(max_length=100, blank=True, null=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sheng_lexicon"

    def to_dict(self):
        return {
            "sheng_term": self.sheng_term,
            "swahili_equivalent": self.swahili_equivalent,
            "english_equivalent": self.english_equivalent,
            "frequency": self.frequency,
            "verified": self.verified,
        }


class IngestionLog(models.Model):
    """Tracks each ingestion run for monitoring and debugging."""

    STATUS_CHOICES = [
        ("running", "Running"),
        ("success", "Success"),
        ("partial", "Partial"),
        ("failed", "Failed"),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    sources_attempted = models.IntegerField(default=0)
    articles_fetched = models.IntegerField(default=0)
    articles_stored = models.IntegerField(default=0)
    articles_embedded = models.IntegerField(default=0)
    errors = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")

    class Meta:
        db_table = "ingestion_logs"

    def to_dict(self):
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "articles_fetched": self.articles_fetched,
            "articles_stored": self.articles_stored,
            "status": self.status,
        }
