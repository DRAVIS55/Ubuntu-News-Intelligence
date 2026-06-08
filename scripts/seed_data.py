"""
scripts/seed_data.py — Seed the database with realistic sample African news articles
Updated to use Django ORM instead of SQLAlchemy.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

import logging
import hashlib
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.progress import track

console = Console()
logging.basicConfig(level=logging.WARNING)

SAMPLE_ARTICLES = [
    # Kenya — Economy
    {
        "source_name": "Business Daily Africa",
        "source_url": "https://businessdailyafrica.com/article/cbs-raises-base-lending-rate-1",
        "title": "CBK raises base lending rate to 13% amid persistent inflation pressure",
        "body": """The Central Bank of Kenya (CBK) Monetary Policy Committee has raised the base lending rate by 50 basis points to 13 percent, citing persistent inflationary pressures and the need to anchor inflation expectations. The decision, announced on Wednesday following the committee's bi-monthly meeting, marks the third consecutive rate hike this year.

CBK Governor Kamau Thugge said the committee noted that inflation, while declining, remained above the target range of 2.5 to 7.5 percent. Food prices continue to exert upward pressure on the consumer price index, with the food and non-alcoholic beverages index rising 11.2 percent year-on-year.

The lending rate increase will push the cost of credit higher for both businesses and households. The Kenya Bankers Association warned that the move would dampen private sector credit growth, which has already slowed to 9.8 percent from 12.3 percent a year earlier.

Treasury Cabinet Secretary John Mbadi defended the decision, saying it was necessary to protect the shilling and contain the cost of living. The shilling has stabilised at around 129 to the dollar following a sharp depreciation earlier in the year.

The IMF, which has a $941 million programme with Kenya, said the rate decision was consistent with Kenya's reform commitments and would help restore macroeconomic stability.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=2),
        "country_code": "KE",
        "category": "business",
    },
    {
        "source_name": "Nation Africa",
        "source_url": "https://nation.africa/kenya/news/cbk-rates-2017-economy",
        "title": "CBK holds rates at 10% as economy shows signs of recovery",
        "body": """The Central Bank of Kenya has held its benchmark lending rate at 10 percent, signalling confidence in the economy's resilience despite external headwinds from weak commodity prices and drought. The decision was unanimous among the Monetary Policy Committee members.

Governor Patrick Njoroge said the committee observed that inflation was within the target band and that the economy was growing at 5.8 percent, in line with projections. Private sector credit growth remained healthy at 4.1 percent, recovering from the impact of the interest rate cap introduced in 2016.

The rate cap law, which limited bank lending rates to 4 percentage points above the CBK base rate, has been controversial since its enactment. Commercial banks have responded by tightening credit to perceived higher-risk borrowers, including small and medium enterprises and individuals without formal employment.

Treasury Principal Secretary Kamau Thugge said the government was studying the effects of the rate cap and would make a recommendation to Parliament.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=365 * 7),
        "country_code": "KE",
        "category": "business",
    },
    # Kenya — Fuel
    {
        "source_name": "The Standard",
        "source_url": "https://standardmedia.co.ke/article/fuel-prices-rise-kenya-epra",
        "title": "EPRA raises petrol price to Sh207 per litre in monthly review",
        "body": """The Energy and Petroleum Regulatory Authority (EPRA) has raised the pump price of petrol in Nairobi to Sh207.40 per litre for the period running from the 15th of this month to the 14th of next month. Diesel prices have been set at Sh193.90 while kerosene rises to Sh168.30.

The increases reflect higher landed costs of petroleum products, driven by rising international crude oil prices and the depreciation of the Kenya shilling against the US dollar. The landed cost of super petrol rose by $42 per cubic metre.

Transport sector players, including matatu operators and truck owners, said they would be forced to raise fares and haulage charges. The Kenya Long Distance Truck Owners Association said the increase would add approximately Sh4,000 to the cost of a Nairobi-Mombasa trip.

Lobby groups have called on the government to reduce the heavy tax burden on petroleum products. Fuel taxes in Kenya account for more than 40 percent of the pump price.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=5),
        "country_code": "KE",
        "category": "business",
    },
    # Kenya — Politics
    {
        "source_name": "Nation Africa",
        "source_url": "https://nation.africa/kenya/news/cabinet-secretary-corruption-probe",
        "title": "DCI opens probe into three Cabinet Secretaries over Sh4.2bn procurement scandal",
        "body": """The Directorate of Criminal Investigations has opened formal investigations into three Cabinet Secretaries following allegations of irregular procurement in their respective ministries totalling Sh4.2 billion. The probe centres on contracts awarded without competitive tendering during the financial year.

The Ethics and Anti-Corruption Commission referred the cases to the DCI after its preliminary investigations found sufficient grounds for criminal inquiry. Documents seen by this newspaper indicate that contracts were awarded to companies linked to associates of the cabinet secretaries.

President William Ruto said he was aware of the investigations and would not interfere with the process. He said any public official found to have misappropriated public funds would face full prosecution.

Opposition leader Raila Odinga called the investigations a sign of the government's internal dysfunction and called for the immediate suspension of the three cabinet secretaries pending investigations.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=8),
        "country_code": "KE",
        "category": "politics",
    },
    # Tanzania
    {
        "source_name": "The Citizen TZ",
        "source_url": "https://thecitizen.co.tz/tanzania/news/tanzania-gdp-growth-2024",
        "title": "Tanzania GDP grows 5.4% in Q3 driven by tourism and mining sectors",
        "body": """Tanzania's economy expanded by 5.4 percent in the third quarter, the National Bureau of Statistics reported, underpinned by strong performance in tourism, mining, and financial services.

The tourism sector recorded a 28 percent increase in visitor arrivals, reaching 1.2 million visitors. Revenue from tourism rose to $1.8 billion for the nine-month period.

Gold exports increased by 12 percent by volume amid rising international gold prices. Finance Minister Mwigulu Nchemba said the government remained confident of achieving its full-year growth target. The Bank of Tanzania held its discount rate steady at 7 percent.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=10),
        "country_code": "TZ",
        "category": "business",
    },
    # Uganda
    {
        "source_name": "Daily Monitor UG",
        "source_url": "https://monitor.co.ug/uganda/news/shilling-record-low-2024",
        "title": "Uganda shilling hits record low as import demand outpaces export earnings",
        "body": """The Uganda shilling weakened to a record 3,820 against the US dollar on Thursday, driven by strong import demand for petroleum products and capital goods while coffee export earnings remained below expectations.

Bank of Uganda Governor Michael Atingi-Ego said the central bank was monitoring the situation and had sufficient reserves to intervene if volatility became disorderly.

Uganda imports nearly all of its petroleum requirements, making the oil import bill one of the largest drivers of foreign exchange demand. Finance Minister Matia Kasaijja said the government was accelerating export diversification efforts.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=6),
        "country_code": "UG",
        "category": "business",
    },
    # Rwanda
    {
        "source_name": "The New Times RW",
        "source_url": "https://newtimes.co.rw/rwanda/news/kagame-digital-economy",
        "title": "Rwanda launches $250m digital economy fund to position Kigali as tech hub",
        "body": """President Paul Kagame has launched a $250 million digital economy fund designed to accelerate Rwanda's emergence as a leading technology and innovation hub in Africa.

The fund will be managed by the Rwanda Development Board and is expected to co-invest with private sector partners in fintech, health technology, and digital agriculture.

ICT Minister Paula Ingabire said the fund would prioritise investments that created technology jobs for Rwandan youth. Rwanda currently ranks second in Africa on the World Bank's Ease of Doing Business index.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=12),
        "country_code": "RW",
        "category": "business",
    },
    # Kenya — Health
    {
        "source_name": "Nation Africa",
        "source_url": "https://nation.africa/kenya/news/cholera-outbreak-nairobi-2024",
        "title": "Cholera outbreak spreads to five Nairobi counties as cases top 2,000",
        "body": """A cholera outbreak that began in Mathare informal settlement has spread to five counties in Nairobi, with cumulative cases now exceeding 2,000 and 38 confirmed deaths, the Ministry of Health reported.

Health Cabinet Secretary Susan Nakhumicha declared a public health emergency. Nairobi City County has faced criticism for its failure to maintain water infrastructure in informal settlements, where an estimated 2 million residents rely on water vendors.

The outbreak comes as Kenya prepares for the rainy season, which historically worsens cholera incidence. Doctors at Kenyatta National Hospital said the facility was operating at 140 percent capacity in its isolation ward.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=3),
        "country_code": "KE",
        "category": "health",
    },
    # Kenya — SGR
    {
        "source_name": "Business Daily Africa",
        "source_url": "https://businessdailyafrica.com/article/sgr-loan-china-audit",
        "title": "Auditor General flags Sh500bn SGR loan terms as unfavourable, demands renegotiation",
        "body": """Kenya's Auditor General Nancy Gathungu has flagged the terms of the Sh500 billion loan used to finance the Standard Gauge Railway as highly unfavourable, calling for urgent renegotiation with the Chinese lenders.

The audit report notes that the loan agreement contains clauses that allow the lender to demand early repayment if Kenya fails to maintain certain financial ratios. The Kenya Railways Corporation reported annual revenue of Sh22 billion against debt service obligations of Sh37 billion.

Transport Cabinet Secretary Davis Chirchir said the government was in discussions with the Exim Bank about restructuring the loan. Opposition figures called for a full parliamentary inquiry into the SGR procurement process.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=20),
        "country_code": "KE",
        "category": "business",
    },
    # Ethiopia
    {
        "source_name": "Addis Standard",
        "source_url": "https://addisstandard.com/ethiopia-eritrea-border-2024",
        "title": "Ethiopia-Eritrea border communities report increased movement as tensions ease",
        "body": """Communities along the Ethiopia-Eritrea border have reported a significant increase in cross-border movement of people and goods for the first time since the border was formally reopened following the 2018 peace agreement.

The Afar and Tigray regions have seen the reopening of several crossing points. Aid organisations report that this is facilitating the movement of humanitarian supplies to communities that were previously difficult to reach.

The AU Commission has welcomed the improved relations, noting that the Ethiopia-Eritrea peace was a model for the region. Economic analysts say border normalisation has the potential to boost trade significantly.""",
        "published_at": datetime.now(timezone.utc) - timedelta(days=15),
        "country_code": "ET",
        "category": "politics",
    },
]


def seed():
    from core.database import init_db
    from core.models import Article

    console.print("\n[bold]Initialising ChromaDB...[/bold]")
    init_db()

    console.print("\n[bold]Seeding sample articles...[/bold]")
    stored = 0
    skipped = 0

    for data in track(SAMPLE_ARTICLES, description="Seeding..."):
        raw = f"{data['source_url']}:{data['title']}"
        chroma_id = hashlib.sha256(raw.encode()).hexdigest()[:40]

        if Article.objects.filter(chroma_id=chroma_id).exists():
            skipped += 1
            continue

        Article.objects.create(
            source_name=data["source_name"],
            source_url=data["source_url"],
            title=data["title"],
            body=data["body"],
            published_at=data["published_at"],
            country_code=data["country_code"],
            category=data["category"],
            language="en",
            chroma_id=chroma_id,
            word_count=len(data["body"].split()),
            is_processed=False,
        )
        stored += 1

    console.print(f"   [green]✓[/green] {stored} articles stored, {skipped} already existed")

    console.print("\n[bold]Generating embeddings...[/bold]")
    from ingestion.embedder import embed_articles
    n = embed_articles()
    console.print(f"   [green]✓[/green] {n} articles embedded into ChromaDB")

    console.print("\n[bold]Building article relations...[/bold]")
    from intelligence.relations import run_relation_engine
    relations = run_relation_engine()
    console.print(f"   [green]✓[/green] {relations} relations created")

    from rich.panel import Panel
    console.print(Panel.fit(
        f"[bold green]✓ Seed complete![/bold green]\n\n"
        f"  {stored} articles loaded\n"
        f"  {n} vectors indexed\n"
        f"  {relations} article relations built\n\n"
        "Run [cyan]python run.py[/cyan] and open [cyan]http://localhost:8000[/cyan]",
        border_style="green"
    ))


if __name__ == "__main__":
    seed()
