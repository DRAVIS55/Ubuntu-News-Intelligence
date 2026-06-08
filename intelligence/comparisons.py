"""
intelligence/comparisons.py — Layer 2d: Peer Country Comparison Engine
Fetches World Bank / IMF data and generates structured country comparisons.
Updated to use Django ORM instead of SQLAlchemy.
"""

import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.config import config, EAC_COUNTRIES, WB_INDICATORS
from core.models import CountryMetric
from intelligence.llm import get_llm

logger = logging.getLogger(__name__)

WB_API_BASE = "https://api.worldbank.org/v2"


# ── World Bank Data Fetcher ─────────────────────────────────────────────────────

def fetch_wb_indicator(country_code: str, indicator: str, years: int = 5) -> Optional[float]:
    """
    Fetch a World Bank indicator for a country.
    Returns the most recent non-null value.
    """
    # Check cache first (Django ORM)
    cached = (
        CountryMetric.objects
        .filter(country_code=country_code, indicator_code=indicator)
        .order_by("-year")
        .first()
    )
    if cached and (datetime.now(timezone.utc) - cached.fetched_at).days < 7:
        return cached.value

    # Fetch from World Bank API
    wb_country = EAC_COUNTRIES.get(country_code, {}).get("wb_code", country_code)
    url = f"{WB_API_BASE}/country/{wb_country}/indicator/{indicator}"
    params = {
        "format": "json",
        "mrv": years,
        "per_page": 10,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data or len(data) < 2 or not data[1]:
            return None

        for entry in data[1]:
            if entry.get("value") is not None:
                value = float(entry["value"])
                year = int(entry["date"])

                CountryMetric.objects.create(
                    country_code=country_code,
                    indicator_code=indicator,
                    indicator_name=entry.get("indicator", {}).get("value", ""),
                    value=value,
                    year=year,
                )

                return value

    except Exception as e:
        logger.warning(f"WB API failed for {country_code}/{indicator}: {e}")

    return None


def fetch_eac_comparison(indicator_key: str) -> dict:
    """
    Fetch a specific indicator across all EAC countries.
    """
    indicator_code = WB_INDICATORS.get(indicator_key)
    if not indicator_code:
        logger.error(f"Unknown indicator key: {indicator_key}")
        return {}

    results = {}
    for code in EAC_COUNTRIES:
        value = fetch_wb_indicator(code, indicator_code)
        if value is not None:
            results[code] = value

    return results


# ── Comparison Engine ───────────────────────────────────────────────────────────

def generate_comparison_report(article_text: str, focus_country: str = "KE") -> dict:
    """
    Detect what economic metric is being discussed and generate a peer country comparison.
    """
    llm = get_llm()

    detect_prompt = f"""Read this news article and identify which economic or policy metrics are discussed.
Choose all that apply from this list:
- inflation
- gdp_growth
- gdp_per_capita
- unemployment
- fuel_imports
- current_account
- external_debt
- interest_rate
- none (no economic metric is central to this story)

Article:
{article_text[:2000]}

Return JSON only: {{"indicators": ["inflation", "interest_rate"]}}"""

    detect_response = llm.complete(detect_prompt, max_tokens=100, temperature=0.0)

    try:
        import json
        clean = detect_response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        detected = json.loads(clean).get("indicators", [])
    except Exception:
        detected = []

    if not detected or detected == ["none"]:
        return {
            "applicable": False,
            "reason": "No economic metrics detected in this article.",
        }

    comparison_data = {}
    for indicator_key in detected[:3]:
        data = fetch_eac_comparison(indicator_key)
        if data:
            comparison_data[indicator_key] = data

    if not comparison_data:
        return {
            "applicable": True,
            "indicators_detected": detected,
            "data": {},
            "reason": "World Bank data unavailable for current period.",
        }

    data_summary = []
    for indicator, country_values in comparison_data.items():
        indicator_name = indicator.replace("_", " ").title()
        values_str = ", ".join([
            f"{EAC_COUNTRIES.get(cc, {}).get('name', cc)}: {v:.1f}"
            for cc, v in sorted(country_values.items(), key=lambda x: x[1], reverse=True)
        ])
        data_summary.append(f"{indicator_name}: {values_str}")

    data_text = "\n".join(data_summary)
    focus_name = EAC_COUNTRIES.get(focus_country, {}).get("name", focus_country)

    narrative_prompt = f"""You are an African economics correspondent.

This article discusses economic conditions in {focus_name}.

Here is the latest data comparing {focus_name} to its EAC neighbours:
{data_text}

Write a short, specific comparative analysis (3-4 paragraphs) that:
1. States where {focus_name} ranks among EAC peers for each metric
2. Explains what structural factors cause the differences
3. Notes what policy approaches other countries are using
4. Draws a conclusion about what this means for {focus_name}

Be specific with numbers. Avoid vague language."""

    narrative = llm.complete(narrative_prompt, max_tokens=600, temperature=0.3)

    return {
        "applicable": True,
        "focus_country": focus_country,
        "indicators_detected": detected,
        "data": comparison_data,
        "peer_countries": {
            cc: EAC_COUNTRIES[cc]["name"]
            for cc in comparison_data.get(detected[0], {}).keys()
            if cc in EAC_COUNTRIES
        },
        "narrative": narrative,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Fuel Price Comparison ───────────────────────────────────────────────────────

FUEL_PRICE_DATA = {
    "KE": {"petrol_ksh": 207.4, "diesel_ksh": 193.9, "source": "EPRA Kenya", "date": "2024-11"},
    "TZ": {"petrol_tzs": 3000, "diesel_tzs": 2750, "source": "EWURA Tanzania", "date": "2024-11"},
    "UG": {"petrol_ugx": 5200, "diesel_ugx": 4800, "source": "MEMD Uganda", "date": "2024-11"},
    "RW": {"petrol_rwf": 1350, "diesel_rwf": 1190, "source": "REG Rwanda", "date": "2024-11"},
    "ET": {"petrol_etb": 75.3, "diesel_etb": 63.2, "source": "MOF Ethiopia", "date": "2024-11"},
}

USD_RATES = {
    "KE": 130.0,
    "TZ": 2550.0,
    "UG": 3750.0,
    "RW": 1280.0,
    "ET": 57.0,
}


def get_fuel_comparison() -> dict:
    """
    Return a standardised fuel price comparison across EAC in USD/litre.
    """
    comparison = []
    for cc, data in FUEL_PRICE_DATA.items():
        usd_rate = USD_RATES.get(cc, 1)
        country_name = EAC_COUNTRIES.get(cc, {}).get("name", cc)
        currency = EAC_COUNTRIES.get(cc, {}).get("currency", "")

        local_price_key = [k for k in data if "petrol" in k and currency.lower() in k.lower()]
        if not local_price_key:
            continue

        local_price = data[local_price_key[0]]
        usd_price = local_price / usd_rate

        comparison.append({
            "country": country_name,
            "country_code": cc,
            "petrol_usd_per_litre": round(usd_price, 3),
            "petrol_local": local_price,
            "currency": currency,
            "source": data.get("source"),
            "data_date": data.get("date"),
        })

    comparison.sort(key=lambda x: x["petrol_usd_per_litre"], reverse=True)

    if comparison:
        ke_data = next((c for c in comparison if c["country_code"] == "KE"), None)
        avg = sum(c["petrol_usd_per_litre"] for c in comparison) / len(comparison)
        ke_vs_avg = ((ke_data["petrol_usd_per_litre"] - avg) / avg) * 100 if ke_data else 0
    else:
        avg = 0
        ke_vs_avg = 0

    return {
        "comparison": comparison,
        "eac_average_usd": round(avg, 3),
        "kenya_vs_eac_average_pct": round(ke_vs_avg, 1),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
