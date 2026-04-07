# candidatus-jobs

A Python microservice that scrapes tech job listings from multiple sources, stores them in PostgreSQL, and exposes a REST API with skill-based job recommendations — built to power the [Candidatus](https://github.com/ErickScur/candidatus) platform.

## Features

- **Multi-source scraping** — Gupy, Remotive, Arbeitnow (public APIs) + LinkedIn and Indeed (Playwright)
- **Automatic skill extraction** — keyword matching against a curated tech skill dictionary
- **Recommendation engine** — ranks jobs by skill-intersection score against a user's resume
- **Scheduled daily refresh** — APScheduler runs scrapes at 03:00 UTC and marks stale jobs inactive
- **REST API with API key auth** — paginated job listing, filters, and recommendation endpoint
- **Docker-ready** — single `docker-compose up` to start everything

## Architecture

```
candidatus-jobs/
├── app/
│   ├── main.py           # FastAPI app & routes
│   ├── models.py         # SQLAlchemy Job model
│   ├── schemas.py        # Pydantic response schemas
│   ├── database.py       # DB engine & session
│   ├── config.py         # Settings (env vars)
│   ├── auth.py           # X-API-Key middleware
│   ├── scheduler.py      # APScheduler daily job
│   ├── scrape_runner.py  # Orchestrates all scrapers + stale cleanup
│   ├── skills.py         # Keyword-based skill extraction
│   ├── recommender.py    # Match score logic
│   └── scrapers/
│       ├── base.py       # Abstract scraper + RawJob dataclass
│       ├── gupy.py       # Gupy public API
│       ├── remotive.py   # Remotive public API
│       ├── arbeitnow.py  # Arbeitnow public API
│       ├── linkedin.py   # LinkedIn (Playwright)
│       └── indeed.py     # Indeed (Playwright)
├── alembic/              # DB migrations
├── Dockerfile
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Docker & Docker Compose

### Run with Docker

```bash
cp .env.example .env
# Edit .env and set a strong API_KEY

docker-compose up
```

The API will be available at `http://localhost:8000`.

### Run locally (dev)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# Edit .env with your DATABASE_URL and API_KEY

alembic upgrade head
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/candidatus_jobs` |
| `API_KEY` | Shared secret for `X-API-Key` header | `change-me` |

## API Reference

All endpoints require the `X-API-Key` header.

### `GET /jobs`

Returns a paginated list of active job listings.

**Query params:**

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (default: 1) |
| `page_size` | int | Results per page (default: 20, max: 100) |
| `search` | string | Filter by title or company |
| `remote` | bool | Filter remote-only jobs |
| `level` | string | Filter by level (junior, pleno, senior) |
| `source` | string | Filter by source (gupy, remotive, arbeitnow, linkedin, indeed) |

**Example:**

```bash
curl "http://localhost:8000/jobs?search=react&remote=true" \
  -H "X-API-Key: your-key"
```

```json
{
  "total": 12,
  "page": 1,
  "page_size": 20,
  "items": [...]
}
```

### `GET /jobs/recommended`

Returns jobs ranked by skill-match score against the provided skills.

**Query params:**

| Param | Type | Description |
|-------|------|-------------|
| `skills` | string[] | User skill list (repeat param for multiple) |
| `limit` | int | Max results (default: 10, max: 50) |

**Example:**

```bash
curl "http://localhost:8000/jobs/recommended?skills=python&skills=fastapi&skills=react" \
  -H "X-API-Key: your-key"
```

```json
[
  {
    "id": "...",
    "title": "Senior Full Stack Developer React/FastAPI",
    "company": "Get Mika",
    "match_score": 0.571,
    ...
  }
]
```

**Match score** = `|user_skills ∩ job_skills| / |job_skills|`

### `GET /jobs/{id}`

Returns a single job by UUID.

### `POST /scrape/trigger`

Manually triggers a full scrape run in the background.

### `DELETE /jobs/stale`

Marks jobs not scraped in the last 7 days as inactive.

### `GET /health`

Health check — no auth required.

## Job Sources

| Source | Method | Notes |
|--------|--------|-------|
| [Gupy](https://gupy.io) | Public API | Brazilian job platform, strong for BR tech roles |
| [Remotive](https://remotive.com) | Public API | Remote-first, global |
| [Arbeitnow](https://arbeitnow.com) | Public API | English-speaking jobs in Europe |
| [LinkedIn](https://linkedin.com/jobs) | Playwright | Small batches, random delays to reduce detection |
| [Indeed](https://indeed.com) | Playwright | Same approach as LinkedIn |

> **Note:** LinkedIn and Indeed scraping is against their ToS and may be rate-limited or blocked. Gupy, Remotive, and Arbeitnow are reliable production sources.

## Skill Extraction

Skills are extracted from job titles and descriptions using a curated keyword dictionary covering 80+ technologies (languages, frameworks, databases, cloud, DevOps, AI/ML).

## Candidatus Integration

This service is consumed by the [Candidatus](https://github.com/ErickScur/candidatus) platform. Add these env vars to Candidatus:

```env
JOBS_API_URL=http://localhost:8000
JOBS_API_KEY=your-shared-key
```

The platform calls `/jobs` for the full browser and `/jobs/recommended` (with the user's resume skills) for the dashboard widget.

## License

MIT
