"""Orchestrates all scrapers and persists results to the database."""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal
from app.models import Job, JobSource
from app.scrapers import GupyScraper, RemotiveScraper, ArbeitnowScraper, LinkedInScraper, IndeedScraper
from app.scrapers.base import RawJob
from app.skills import extract_skills

logger = logging.getLogger(__name__)

SCRAPER_SOURCE_MAP = [
    (GupyScraper(), JobSource.gupy),
    (RemotiveScraper(), JobSource.remotive),
    (ArbeitnowScraper(), JobSource.arbeitnow),
    (LinkedInScraper(), JobSource.linkedin),
    (IndeedScraper(), JobSource.indeed),
]


async def _run_scraper(scraper, source: JobSource) -> tuple[JobSource, list[RawJob]]:
    logger.info(f"Running scraper: {source.value}")
    try:
        jobs = await scraper.scrape()
        return source, jobs
    except Exception as e:
        logger.error(f"Scraper {source.value} failed: {e}")
        return source, []


def _persist(db: Session, source: JobSource, raw_jobs: list[RawJob]) -> int:
    count = 0
    for raw in raw_jobs:
        try:
            skills = extract_skills(f"{raw.title} {raw.description}")
            stmt = (
                insert(Job)
                .values(
                    title=raw.title,
                    company=raw.company,
                    location=raw.location,
                    remote=raw.remote,
                    description=raw.description,
                    url=raw.url,
                    source=source,
                    required_skills=skills,
                    job_level=raw.job_level,
                    posted_at=raw.posted_at,
                    scraped_at=datetime.now(timezone.utc),
                    is_active=True,
                )
                .on_conflict_do_update(
                    index_elements=["url"],
                    set_={
                        "title": raw.title,
                        "company": raw.company,
                        "description": raw.description,
                        "required_skills": skills,
                        "scraped_at": datetime.now(timezone.utc),
                        "is_active": True,
                    },
                )
            )
            db.execute(stmt)
            count += 1
        except Exception as e:
            logger.warning(f"Failed to upsert job {raw.url}: {e}")
    db.commit()
    logger.info(f"Scraper {source.value}: {len(raw_jobs)} jobs processed")
    return count


async def run_all_scrapers():
    """Run all scrapers concurrently and upsert results into the database."""
    db = SessionLocal()
    try:
        results = await asyncio.gather(
            *[_run_scraper(scraper, source) for scraper, source in SCRAPER_SOURCE_MAP]
        )
        total = sum(_persist(db, source, jobs) for source, jobs in results)
        mark_stale(db)
        logger.info(f"Scrape run complete. Total upserted: {total}")
    finally:
        db.close()


def mark_stale(db: Session, days: int = 7):
    """Mark jobs not seen in the last `days` days as inactive."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    db.query(Job).filter(Job.scraped_at < cutoff, Job.is_active == True).update(  # noqa: E712
        {"is_active": False}
    )
    db.commit()
