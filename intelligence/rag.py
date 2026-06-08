"""
intelligence/rag.py — Retrieval-Augmented Generation engine
The core of the journalist intelligence tools:
- Headline generation
- Article context briefing
- Historical parallel retrieval
- Research brief generation
- Fact-check assistance

Updated to use Django ORM instead of SQLAlchemy sessions.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from intelligence.llm import get_llm

logger = logging.getLogger(__name__)


# ── Headline Generator ──────────────────────────────────────────────────────────

def generate_headlines(article_text: str, n: int = 5) -> list[dict]:
    """
    Generate multiple headline options for a given article.
    Returns a list of headlines with style labels and scores.
    """
    llm = get_llm()
    body_preview = article_text[:3000].strip()

    prompt = f"""You are a senior news editor at a leading East African newspaper.

Read this article and generate {n} different headline options. Each headline should:
- Be accurate to the article's content
- Be between 8 and 15 words
- Use active voice where possible
- Be specific (avoid vague terms like "officials say")
- Be appropriate for an African readership

Article:
{body_preview}

Respond in this exact JSON format (no preamble, no explanation):
{{
  "headlines": [
    {{"text": "...", "style": "straight_news", "explanation": "..."}},
    {{"text": "...", "style": "contextual", "explanation": "..."}},
    {{"text": "...", "style": "data_led", "explanation": "..."}},
    {{"text": "...", "style": "impact_led", "explanation": "..."}},
    {{"text": "...", "style": "question", "explanation": "..."}}
  ]
}}

Style definitions:
- straight_news: Classic news headline, most factual
- contextual: Places event in broader context
- data_led: Leads with a specific number or statistic
- impact_led: Emphasises effect on ordinary people
- question: Poses the key question the story answers"""

    response = llm.complete(prompt, temperature=0.4, max_tokens=800)

    try:
        import json
        clean = response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        data = json.loads(clean)
        return data.get("headlines", [])
    except Exception as e:
        logger.error(f"Headline JSON parse failed: {e}\nResponse: {response[:200]}")
        return [{"text": response.strip()[:150], "style": "unknown", "explanation": ""}]


# ── Historical Context Brief ────────────────────────────────────────────────────

def get_context_brief(article_text: str, article_title: str = "") -> dict:
    """
    Generate a historical context brief for a news article.
    Searches the archive for similar past events and produces a structured brief.
    """
    from ingestion.embedder import semantic_search
    from core.models import Article

    llm = get_llm()

    query = f"{article_title} {article_text[:500]}"
    similar = semantic_search(query, n_results=8)

    context_articles = []
    if similar:
        article_ids = [int(r["article_id"]) for r in similar if r.get("article_id")]
        for aid in article_ids[:5]:
            try:
                art = Article.objects.get(id=aid)
                context_articles.append({
                    "title": art.title,
                    "source": art.source_name,
                    "date": art.published_at.strftime("%B %Y") if art.published_at else "Unknown",
                    "body": art.body[:800],
                })
            except Article.DoesNotExist:
                pass

    archive_context = (
        "\n\n".join([
            f"--- {a['date']} | {a['source']} ---\n{a['title']}\n{a['body']}"
            for a in context_articles
        ])
        if context_articles
        else "No directly related historical articles found in archive."
    )

    prompt = f"""You are a senior African news analyst briefing a journalist before they write their article.

CURRENT ARTICLE:
{article_text[:2000]}

RELATED HISTORICAL ARCHIVE (from our news database):
{archive_context}

Based on this, produce a structured journalist briefing with these sections:
1. WHAT THIS IS ABOUT (2-3 sentences, plain language)
2. HISTORICAL PARALLELS (specific past events this resembles, with dates)
3. KEY ACTORS (who is involved and what is their track record)
4. REGIONAL CONTEXT (how does this fit East Africa's broader picture)
5. WHAT TYPICALLY HAPPENS NEXT (based on historical patterns)
6. WHAT TO INVESTIGATE (3-5 questions a journalist should pursue)
7. DATA POINTS (specific numbers, statistics, or benchmarks relevant to this story)

Be specific. Cite dates and sources where available. Do not speculate."""

    response = llm.complete(prompt, max_tokens=1500, temperature=0.2)

    return {
        "brief": response,
        "historical_matches": similar[:5],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Research Brief Generator ────────────────────────────────────────────────────

def generate_research_brief(topic: str, country_code: str = "KE") -> dict:
    """
    Generate a one-page research brief on any topic.
    Draws from the archive and LLM knowledge.
    """
    from ingestion.embedder import semantic_search
    from core.models import Article

    llm = get_llm()

    similar = semantic_search(topic, n_results=10, country_code=country_code)

    archive_summaries = []
    if similar:
        article_ids = [int(r["article_id"]) for r in similar if r.get("article_id")]
        for aid in article_ids[:6]:
            try:
                art = Article.objects.get(id=aid)
                archive_summaries.append(
                    f"[{art.published_at.strftime('%d %b %Y') if art.published_at else '?'}] "
                    f"{art.title} ({art.source_name})\n{art.body[:400]}"
                )
            except Article.DoesNotExist:
                pass

    archive_context = "\n\n".join(archive_summaries) if archive_summaries else "No archive data found."

    prompt = f"""You are preparing a one-page research brief for a journalist covering {topic} in {country_code}.

ARCHIVE CONTEXT:
{archive_context}

Generate a comprehensive research brief with:

# TOPIC: {topic}

## Executive Summary
(3-4 sentences)

## Background
(Key historical context, 2-3 paragraphs)

## Key Players
(Who are the main actors: government, private sector, civil society)

## Timeline of Key Events
(Chronological list of significant developments)

## The Numbers
(Key statistics, budgets, volumes, percentages)

## Regional Comparison
(How does this compare to Tanzania, Uganda, Rwanda?)

## Controversies and Disputes
(What is contested or disputed)

## What to Watch
(3-5 upcoming milestones or developments)

## Recommended Sources
(Experts, institutions, databases to consult)

Be precise, factual, and useful to a working journalist."""

    response = llm.complete(prompt, max_tokens=2000, temperature=0.2)

    return {
        "topic": topic,
        "country_code": country_code,
        "brief": response,
        "archive_sources": similar[:5],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Article Rewriter ────────────────────────────────────────────────────────────

def rewrite_article(article_text: str, style: str = "standard") -> dict:
    """
    Improve a draft article: clarity, structure, active voice.

    Args:
        article_text: The draft article text
        style: 'standard' | 'concise' | 'investigative'
    """
    llm = get_llm()

    style_instructions = {
        "standard": "Clear, direct news writing. Inverted pyramid structure.",
        "concise": "Maximum information density. Cut all unnecessary words.",
        "investigative": "Methodical, evidence-led. Every claim attributed or evidenced.",
    }

    prompt = f"""You are a senior editor at a leading African newspaper.
Rewrite the following article in {style} style: {style_instructions.get(style, '')}

Rules:
- Use active voice
- Put the most important information first
- Remove jargon and bureaucratic language
- Replace vague phrases with specific ones ("several" → actual number if stated)
- Ensure every major claim has a source
- Flag [NEEDS SOURCE] where a claim lacks attribution
- Flag [VERIFY] where a factual claim should be checked

ORIGINAL DRAFT:
{article_text[:4000]}

Return:
1. REWRITTEN ARTICLE (full text)
2. CHANGES MADE (bullet list of key edits)
3. GAPS FLAGGED (unverified claims or missing sources)"""

    response = llm.complete(prompt, max_tokens=2000, temperature=0.2)

    return {
        "rewritten": response,
        "style": style,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Fact-Check Assistant ────────────────────────────────────────────────────────

def fact_check_article(article_text: str) -> dict:
    """
    Cross-reference claims in an article against the indexed archive.
    Returns a list of claims with their verification status.
    """
    from ingestion.embedder import semantic_search

    llm = get_llm()

    # Step 1: Extract claims
    extract_prompt = f"""Extract the 5-8 most important factual claims from this article.
For each claim, return it as a short statement that can be searched.

Article:
{article_text[:3000]}

Return JSON:
{{"claims": ["claim 1", "claim 2", ...]}}"""

    claims_response = llm.complete(extract_prompt, max_tokens=400, temperature=0.1)

    try:
        import json
        clean = claims_response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        claims_data = json.loads(clean)
        claims = claims_data.get("claims", [])
    except Exception:
        claims = [article_text[:200]]

    # Step 2: Search archive for each claim
    results = []
    for claim in claims[:6]:
        similar = semantic_search(claim, n_results=3)
        evidence = [
            {
                "title": r["title"],
                "source": r["source_name"],
                "date": r["published_at"],
                "similarity": r["similarity"],
            }
            for r in similar
            if r["similarity"] > 0.5
        ]
        results.append({
            "claim": claim,
            "archive_evidence": evidence,
            "evidence_found": len(evidence) > 0,
        })

    # Step 3: LLM synthesis
    evidence_summary = "\n".join([
        f"Claim: {r['claim']}\n"
        f"Evidence: {len(r['archive_evidence'])} matching articles found\n"
        f"Top match: {r['archive_evidence'][0]['title'] if r['archive_evidence'] else 'None'}"
        for r in results
    ])

    synthesis_prompt = f"""As a fact-checker for an African newspaper, assess these claims:

{evidence_summary}

For each claim, rate it:
- SUPPORTED: Archive evidence corroborates the claim
- UNVERIFIED: No archive evidence found (requires further verification)
- CONTRADICTED: Archive evidence contradicts the claim
- PLAUSIBLE: Claim fits known context but cannot be directly verified

Keep your assessment brief and actionable."""

    synthesis = llm.complete(synthesis_prompt, max_tokens=600, temperature=0.1)

    return {
        "claims": results,
        "synthesis": synthesis,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
