import asyncio
import logging
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
from app.scrape_runner import run_all_scrapers

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Candidatus Jobs API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jobs", response_model=JobsPage, dependencies=[Depends(require_api_key)])
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    remote: bool | None = Query(None),
    level: str | None = Query(None),
    source: str | None = Query(None),
    skill: str | None = Query(None),
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


@app.get("/jobs/recommended", response_model=list[JobRecommended], dependencies=[Depends(require_api_key)])
def recommended_jobs(
    skills: list[str] = Query(...),
    limit: int = Query(10, ge=1, le=50),
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


@app.get("/jobs/{job_id}", response_model=JobOut, dependencies=[Depends(require_api_key)])
def get_job(job_id: str, db: Session = Depends(get_db)):
    import uuid
    try:
        uid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    job = db.query(Job).filter(Job.id == uid, Job.is_active == True).first()  # noqa: E712
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.delete("/jobs/stale", dependencies=[Depends(require_api_key)])
def delete_stale(db: Session = Depends(get_db)):
    from app.scrape_runner import mark_stale
    mark_stale(db)
    return {"message": "Stale jobs marked inactive"}


@app.post("/scrape/trigger", dependencies=[Depends(require_api_key)])
async def trigger_scrape():
    asyncio.create_task(run_all_scrapers())
    return {"message": "Scrape started in background"}
