import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.auth import require_api_key
from app.database import get_db
from app.models import Job
from app.recommender import compute_match_score
from app.schemas import JobOut, JobRecommended, JobsPage
from app.scheduler import start_scheduler, stop_scheduler
from app.scrape_runner import run_all_scrapers, mark_stale

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Candidatus Jobs API",
    description=(
        "Aggregates job listings scraped from LinkedIn, Indeed, Gupy, Remotive, and Arbeitnow. "
        "Provides filtering, full-text search, and skill-based recommendation.\n\n"
        "All endpoints except `/health` require an `X-API-Key` header."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/health",
    summary="Health check",
    tags=["System"],
)
def health():
    return {"status": "ok"}


@app.get(
    "/jobs",
    response_model=JobsPage,
    summary="List jobs",
    description=(
        "Returns a paginated list of active job listings. "
        "Supports filtering by remote, seniority level, source platform, skill, and free-text search."
    ),
    tags=["Jobs"],
    dependencies=[Depends(require_api_key)],
)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    search: str | None = Query(None, description="Free-text search on title and company"),
    remote: bool | None = Query(None, description="Filter by remote availability"),
    level: str | None = Query(None, description="Filter by seniority level (e.g. `junior`, `senior`)"),
    source: str | None = Query(None, description="Filter by source platform (e.g. `linkedin`, `gupy`)"),
    skill: str | None = Query(None, description="Filter jobs that require this skill"),
    db: Session = Depends(get_db),
):
    q = db.query(Job).filter(Job.is_active == True)  # noqa: E712

    if search:
        term = f"%{search.lower()}%"
        q = q.filter(or_(func.lower(Job.title).like(term), func.lower(Job.company).like(term)))
    if remote is not None:
        q = q.filter(Job.remote == remote)
    if level:
        q = q.filter(func.lower(Job.job_level) == level.lower())
    if source:
        q = q.filter(Job.source == source)
    if skill:
        q = q.filter(Job.required_skills.any(func.lower(skill)))

    total = q.count()
    items = q.order_by(Job.scraped_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return JobsPage(total=total, page=page, page_size=page_size, items=items)


@app.get(
    "/jobs/recommended",
    response_model=list[JobRecommended],
    summary="Skill-based job recommendations",
    description=(
        "Returns the top N jobs ranked by skill overlap with the provided skill list. "
        "Only jobs that have at least one extracted skill are considered."
    ),
    tags=["Jobs"],
    dependencies=[Depends(require_api_key)],
)
def recommended_jobs(
    skills: list[str] = Query(..., description="Skills to match against (repeat the param for multiple)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
):
    if not skills:
        raise HTTPException(status_code=400, detail="At least one skill is required")

    jobs = db.query(Job).filter(Job.is_active == True).all()  # noqa: E712
    scored = [
        (job, compute_match_score(job, skills))
        for job in jobs
        if job.required_skills
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]

    return [
        JobRecommended(**JobOut.model_validate(job).model_dump(), match_score=round(score, 3))
        for job, score in top
    ]


@app.get(
    "/jobs/{job_id}",
    response_model=JobOut,
    summary="Get a job by ID",
    tags=["Jobs"],
    responses={
        400: {"description": "Invalid UUID format"},
        404: {"description": "Job not found or inactive"},
    },
    dependencies=[Depends(require_api_key)],
)
def get_job(job_id: str, db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    job = db.query(Job).filter(Job.id == uid, Job.is_active == True).first()  # noqa: E712
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.delete(
    "/jobs/stale",
    summary="Mark stale jobs inactive",
    description="Deactivates job listings that have not been seen in recent scrape runs.",
    tags=["Jobs"],
    dependencies=[Depends(require_api_key)],
)
def delete_stale(db: Session = Depends(get_db)):
    mark_stale(db)
    return {"message": "Stale jobs marked inactive"}


@app.post(
    "/scrape/trigger",
    summary="Trigger a scrape run",
    description="Starts a full scrape across all configured sources in the background.",
    tags=["Scraping"],
    dependencies=[Depends(require_api_key)],
)
async def trigger_scrape():
    asyncio.create_task(run_all_scrapers())
    return {"message": "Scrape started in background"}
