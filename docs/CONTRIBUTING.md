# Contributing to the African News Intelligence Platform

Thank you for wanting to contribute. This project is African-built and African-owned. We welcome contributions from developers, journalists, linguists, and data specialists across the continent.

---

## Areas of Greatest Need

### 1. Swahili and Sheng NLP Data

The platform's language capability is only as good as its training data.

**Swahili:**
- Kenyan parliamentary Hansard in Swahili
- Court proceedings in Swahili
- News articles from Taifa Leo, Mwananchi (Tanzania), Bukedde (Uganda)
- If you have access to any of these, open an issue and let's discuss

**Sheng:**
- Sheng-to-English or Sheng-to-Swahili translation pairs
- Sheng glossary entries with usage examples
- Social media Sheng posts (with consent for research use)
- Contribute via the `/api/v1/sheng/contribute` endpoint (coming in v0.4)

### 2. African News Source Scrapers

We need scrapers for sources not yet covered. Priority list:

| Country | Source | Status |
|---|---|---|
| Ghana | Graphic Online | Needed |
| Nigeria | Punch, Vanguard, The Nation | Needed |
| South Africa | Mail & Guardian, Daily Maverick | Needed |
| Senegal | Le Soleil (French) | Needed |
| DRC | Radio Okapi | Needed |
| Somalia | Garowe Online | Needed |

To add a source:
1. Add its RSS feed URL to `core/config.py` in the `NEWS_SOURCES` list
2. Test that articles parse correctly: `python -c "from ingestion.scraper import fetch_rss_feed; print(fetch_rss_feed({'name':'Test','url':'YOUR_RSS_URL','country':'GH','category':'general'}))"`
3. Open a PR

### 3. Fine-tuning Experiments

We want to track fine-tuning experiments systematically. If you run a fine-tuning experiment:

- Use `scripts/fine_tune.py` as the base
- Log your hyperparameters and results in `docs/experiments/`
- Use the naming convention: `YYYYMMDD_model_task_notes.md`
- Include: base model, dataset size, training time, hardware used, evaluation metric, and qualitative assessment

### 4. Journalist Testing

We need feedback from working journalists. If you are a journalist willing to test:

- Contact us to get beta access
- Try the headline generator, context brief, and fact-check assistant on real articles
- Fill in the feedback form (link in dashboard)
- Report what is wrong, what is missing, and what would make you use this daily

---

## Development Setup

```bash
git clone https://github.com/your-org/african-news-intel
cd african-news-intel
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
# Edit .env with your credentials
python scripts/init_db.py
python scripts/seed_data.py
pytest tests/ -v
python run.py
```

---

## Code Standards

- **Python 3.10+** — use type hints where practical
- **Docstrings** — every public function gets a one-line docstring minimum
- **Tests** — new features need a test in `tests/`
- **No secrets in code** — all credentials go in `.env`
- **African context first** — if a feature only makes sense for a Western context, reconsider it

---

## Pull Request Process

1. Fork the repo and create a branch: `git checkout -b feature/your-feature-name`
2. Make your changes with tests
3. Run the full test suite: `pytest tests/ -v`
4. Update the README if you're adding a feature
5. Open a PR with a clear description of what you changed and why
6. Reference any relevant issues

---

## Data Contribution

If you have a large dataset (historical newspaper archives, government documents, court records in Swahili), do not upload it to GitHub. Open an issue titled "Dataset contribution: [description]" and we will arrange a secure transfer.

All data contributors will be credited in `docs/DATA_SOURCES.md`.

---

## Code of Conduct

This project is for African journalists and communities. We expect all contributors to:

- Treat other contributors with respect
- Be specific and constructive in code reviews
- Understand that contributors span many time zones and response times vary
- Not use the platform or its data for surveillance, disinformation, or political manipulation

---

## Licence

This project is licensed under the MIT Licence. By contributing, you agree that your contributions will be licenced under the same terms.

---

*Built in Nairobi. Open to the continent.*
