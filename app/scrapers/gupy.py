"""Gupy public API scraper — https://portal.api.gupy.io"""
import httpx
from app.scrapers.base import BaseScraper, RawJob

SEARCH_TERMS = ["desenvolvedor", "developer", "engenheiro", "engineer", "data", "backend", "frontend"]
BASE_URL = "https://portal.api.gupy.io/api/v1/jobs"


class GupyScraper(BaseScraper):
    async def scrape(self) -> list[RawJob]:
        jobs: dict[str, RawJob] = {}
        async with httpx.AsyncClient(timeout=30) as client:
            for term in SEARCH_TERMS:
                try:
                    resp = await client.get(BASE_URL, params={"jobName": term, "limit": 100})
                    resp.raise_for_status()
                    data = resp.json()
                    for item in data.get("data", []):
                        url = item.get("jobUrl") or item.get("careerPageUrl", "")
                        if not url or url in jobs:
                            continue
                        posted_at = None
                        if pub_date := item.get("publishedDate"):
                            try:
                                from datetime import datetime, timezone
                                posted_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                            except Exception:
                                pass
                        jobs[url] = RawJob(
                            title=item.get("name", ""),
                            company=item.get("careerPageName", ""),
                            description=item.get("description") or item.get("name", ""),
                            url=url,
                            location=item.get("city"),
                            remote=bool(item.get("isRemoteWork")) or item.get("workplaceType", "").lower() in ("remote", "remoto"),
                            posted_at=posted_at,
                        )
                except Exception:
                    continue
        return list(jobs.values())
