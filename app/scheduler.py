import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def _run_scrape():
    from app.scrape_runner import run_all_scrapers
    asyncio.run(run_all_scrapers())


def start_scheduler():
    scheduler.add_job(
        _run_scrape,
        trigger=CronTrigger(hour=3, minute=0, timezone="UTC"),
        id="daily_scrape",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — daily scrape at 03:00 UTC")


def stop_scheduler():
    scheduler.shutdown(wait=False)
