# African News Intelligence Platform

> A sovereign, Africa-native AI system that understands news the way an African journalist thinks — with historical memory, regional context, and the ability to connect dots across time, countries, and economic realities.

---

## Quick Start

### Prerequisites

- Python 3.10+
- 8GB RAM minimum (16GB recommended for local model)
- Optional: CUDA GPU for faster inference

### Installation

```bash
# Clone the repo
git clone https://github.com/DRAVIS55/Ubuntu-News-Intelligence.git
cd african-news-intel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up environment
cp .env.example .env
# Edit .env with your API keys (see Configuration section)

# Initialize the database
python scripts/init_db.py

# Seed sample data
python scripts/seed_data.py

# Start the platform
python run.py
```

Open [http://localhost:8000](http://localhost:8000)

---

## Architecture

```
african-news-intel/
├── ingestion/          # Layer 1: Data ingestion & archive
│   ├── scraper.py      # RSS + web scraper
│   ├── embedder.py     # Vector embedding generator
│   └── scheduler.py    # Cron-based ingestion scheduler
│
├── intelligence/       # Layer 2: AI Intelligence Core
│   ├── rag.py          # Retrieval-Augmented Generation engine
│   ├── relations.py    # Relation & knowledge graph engine
│   ├── comparisons.py  # Peer country comparison engine
│   ├── patterns.py     # Trend & pattern detection
│   └── llm.py          # LLM abstraction layer
│
├── core/               # Shared utilities
│   ├── database.py     # PostgreSQL + ChromaDB connectors
│   ├── models.py       # SQLAlchemy data models
│   └── config.py       # Configuration management
│
├── api/                # Layer 4: REST API
│   ├── routes.py       # All API endpoints
│   └── middleware.py   # Auth, rate limiting, CORS
│
├── dashboard/          # Journalist web interface
│   ├── app.py          # Django app
│   └── static/         # HTML/CSS/JS frontend
│
├── scripts/            # Utility scripts
│   ├── init_db.py      # Database initialisation
│   ├── seed_data.py    # Sample data seeder
│   └── fine_tune.py    # Model fine-tuning script
│
└── tests/              # Test suite
```

---

## Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `CHROMA_PATH` | ChromaDB storage directory | Yes |
| `LLM_PROVIDER` | `anthropic`, `openai`, or `local` | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | If using Anthropic |
| `OPENAI_API_KEY` | OpenAI API key | If using OpenAI |
| `LOCAL_MODEL_PATH` | Path to local GGUF model | If using local |
| `WORLD_BANK_API_KEY` | World Bank API key | Optional |
| `NEWS_API_KEY` | NewsAPI.org key | Optional |
| `SECRET_KEY` | Django secret key | Yes |

---

## Features

### Journalist Dashboard
- **Headline Generator** — Paste article text, get ranked headline options
- **Context Brief** — Automatic historical context for any story
- **Peer Comparison** — How Kenya's metrics compare to EAC countries
- **Archive Search** — Semantic search over indexed articles
- **Pattern Alerts** — Automatically detected trends and anomalies

### REST API
All features are accessible via REST API for CMS integration.

### Supported Languages
- English (full)
- Swahili (full with multilingual model)
- Code-switching / mixed English-Swahili
- Sheng (experimental, corpus collection mode)

---

## LLM Providers

The platform supports three modes:

### 1. Cloud API (Recommended for getting started)
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
```

### 2. Local Model (Recommended for production/sovereignty)
Download a GGUF model (e.g., Mistral-7B-Instruct):
```bash
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf -O models/mistral-7b.gguf
```
```env
LLM_PROVIDER=local
LOCAL_MODEL_PATH=models/mistral-7b.gguf
```

### 3. Fine-tuned African Model
After collecting training data, run:
```bash
python scripts/fine_tune.py --base-model mistral-7b --data data/african_news_training.jsonl
```

---

## Data Sovereignty

This platform is designed to run entirely on African infrastructure:
- PostgreSQL runs on your server
- ChromaDB stores vectors locally
- Local LLM mode uses no external APIs
- All journalist queries stay on-premise

Recommended deployment: Safaricom Cloud or a co-located server in a Nairobi data centre.

---

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

Areas where contributions are most needed:
- Swahili and Sheng NLP datasets
- Additional African news source scrapers
- Fine-tuning experiments
- Journalist UX testing

---

*Built in Nairobi. For African journalism.*
