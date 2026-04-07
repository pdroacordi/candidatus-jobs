"""LinkedIn job scraper using Playwright.

LinkedIn aggressively blocks scrapers. This implementation uses Playwright
with random delays and a realistic user-agent. Batches are kept small to
reduce detection risk. Expect occasional CAPTCHAs or blocks.
"""
import asyncio
import random
from app.scrapers.base import BaseScraper, RawJob

SEARCH_QUERIES = [
    "software engineer",
    "backend developer",
    "frontend developer",
    "data engineer",
    "fullstack developer",
]
MAX_JOBS_PER_QUERY = 10


class LinkedInScraper(BaseScraper):
    async def scrape(self) -> list[RawJob]:
        from playwright.async_api import async_playwright

        jobs: dict[str, RawJob] = {}
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            for query in SEARCH_QUERIES:
                try:
                    page = await context.new_page()
                    url = (
                        f"https://www.linkedin.com/jobs/search/"
                        f"?keywords={query.replace(' ', '%20')}&f_TPR=r86400"
                    )
                    await page.goto(url, timeout=30000)
                    await asyncio.sleep(random.uniform(3, 6))

                    job_cards = await page.query_selector_all(".job-search-card")
                    count = 0
                    for card in job_cards:
                        if count >= MAX_JOBS_PER_QUERY:
                            break
                        try:
                            a_el = await card.query_selector("a.base-card__full-link")
                            title_el = await card.query_selector(".base-search-card__title")
                            company_el = await card.query_selector(".base-search-card__subtitle")
                            location_el = await card.query_selector(".job-search-card__location")

                            href = await a_el.get_attribute("href") if a_el else None
                            if not href or href in jobs:
                                continue
                            title = (await title_el.inner_text()).strip() if title_el else query
                            company = (await company_el.inner_text()).strip() if company_el else ""
                            location = (await location_el.inner_text()).strip() if location_el else None

                            jobs[href] = RawJob(
                                title=title,
                                company=company,
                                description=title,
                                url=href,
                                location=location,
                                remote="remote" in (location or "").lower(),
                            )
                            count += 1
                        except Exception:
                            continue

                    await page.close()
                    await asyncio.sleep(random.uniform(5, 10))
                except Exception:
                    continue

            await browser.close()
        return list(jobs.values())
