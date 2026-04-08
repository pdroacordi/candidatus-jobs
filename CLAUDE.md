# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Candidatus-jobs is a Python microservice that scrapes tech job listings from 5 sources, stores them in PostgreSQL, and serves them via a REST API with skill-based recommendations. It integrates with the parent Candidatus platform.

## Common Commands

```bash
# Run locally
uvicorn app.main:app --reload

# Run with Docker
docker-compose up

# Database migrations
alembic upgrade head                    # Apply all migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Manual scrape trigger
curl -X POST http://localhost:8000/scrape/trigger -H "X-API-Key: $API_KEY"
```

There is no test suite, linter config, or Makefile in this project.

## Architecture

**Stack:** FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + APScheduler + Playwright (Python 3.12)

**Data flow:**
```
Scheduler (daily 3am UTC) or POST /scrape/trigger
  → run_all_scrapers() via asyncio.gather (concurrent)
    → 3 API scrapers (Gupy, Remotive, Arbeitnow) + 2 Playwright scrapers (LinkedIn, Indeed)
  → extract_skills() from title + description (regex word-match against 80+ keywords)
  → upsert to jobs table (unique on url)
  → mark_stale() deactivates jobs older than 7 days
```

**Key modules:**
- `app/main.py` — FastAPI app, routes, lifespan (scheduler start/stop)
- `app/scrape_runner.py` — Scraper orchestration, DB upsert, stale marking
- `app/scrapers/base.py` — Abstract `BaseScraper` + `RawJob` dataclass
- `app/scrapers/*.py` — Individual scraper implementations
- `app/recommender.py` — Score = |user_skills ∩ job_skills| / |job_skills|, min 3 skills
- `app/skills.py` — Static skill dictionary for extraction
- `app/auth.py` — X-API-Key header authentication
- `app/models.py` — Single `Job` model (UUID PK, ARRAY skills column)
- `app/database.py` — SQLAlchemy engine & session factory
- `app/config.py` — Pydantic Settings (reads from env)

**API endpoints** (all except /health require X-API-Key header):
- `GET /jobs` — Paginated listing with filters (search, remote, level, source, skill)
- `GET /jobs/recommended?skills=python,react` — Skill-ranked results
- `GET /jobs/{id}` — Single job
- `POST /scrape/trigger` — Manual scrape (runs as background task)
- `DELETE /jobs/stale` — Mark old jobs inactive
- `GET /health` — Health check (no auth)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `API_KEY` | Shared secret for X-API-Key auth |

See `.env.example` for defaults.

## Deployment

- **Docker:** Multi-stage build, runs `alembic upgrade head` on startup, exposes `$PORT` (default 8000)
- **Railway:** Configured via `railway.toml`, health check on `/health`
