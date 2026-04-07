"""Remotive public API — https://remotive.com/api/remote-jobs"""
import httpx
from datetime import datetime, timezone
from app.scrapers.base import BaseScraper, RawJob

API_URL = "https://remotive.com/api/remote-jobs"
CATEGORIES = ["software-dev", "data", "devops-sysadmin", "product"]


class RemotiveScraper(BaseScraper):
    async def scrape(self) -> list[RawJob]:
        jobs: dict[str, RawJob] = {}
        async with httpx.AsyncClient(timeout=30) as client:
            for category in CATEGORIES:
                try:
                    resp = await client.get(API_URL, params={"category": category, "limit": 100})
                    resp.raise_for_status()
                    data = resp.json()
                    for item in data.get("jobs", []):
                        url = item.get("url", "")
                        if not url or url in jobs:
                            continue
                        posted_at = None
                        if pub_date := item.get("publication_date"):
                            try:
                                posted_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                            except Exception:
                                pass
                        jobs[url] = RawJob(
                            title=item.get("title", ""),
                            company=item.get("company_name", ""),
                            description=item.get("description", ""),
                            url=url,
                            remote=True,
                            posted_at=posted_at,
                        )
                except Exception:
                    continue
        return list(jobs.values())
