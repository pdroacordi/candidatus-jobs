"""Arbeitnow public API — https://www.arbeitnow.com/api/job-board-api"""
import httpx
from datetime import datetime, timezone
from app.scrapers.base import BaseScraper, RawJob

API_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowScraper(BaseScraper):
    async def scrape(self) -> list[RawJob]:
        jobs: dict[str, RawJob] = {}
        async with httpx.AsyncClient(timeout=30) as client:
            page = 1
            while page <= 3:  # fetch up to 3 pages (~300 jobs)
                try:
                    resp = await client.get(API_URL, params={"page": page})
                    resp.raise_for_status()
                    data = resp.json()
                    items = data.get("data", [])
                    if not items:
                        break
                    for item in items:
                        url = item.get("url", "")
                        if not url or url in jobs:
                            continue
                        posted_at = None
                        if ts := item.get("created_at"):
                            try:
                                posted_at = datetime.fromtimestamp(ts, tz=timezone.utc)
                            except Exception:
                                pass
                        jobs[url] = RawJob(
                            title=item.get("title", ""),
                            company=item.get("company_name", ""),
                            description=item.get("description", ""),
                            url=url,
                            location=item.get("location"),
                            remote=bool(item.get("remote")),
                            posted_at=posted_at,
                        )
                    page += 1
                except Exception:
                    break
        return list(jobs.values())
