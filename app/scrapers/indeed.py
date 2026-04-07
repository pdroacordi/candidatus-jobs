"""Indeed job scraper using Playwright.

Indeed also blocks scrapers. Same strategy as LinkedIn: small batches, random delays.
"""
import asyncio
import random
from app.scrapers.base import BaseScraper, RawJob

SEARCH_QUERIES = ["software engineer", "backend developer", "data engineer", "frontend developer"]
MAX_JOBS_PER_QUERY = 10


class IndeedScraper(BaseScraper):
    async def scrape(self) -> list[RawJob]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return []

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
                    url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&sort=date"
                    await page.goto(url, timeout=30000)
                    await asyncio.sleep(random.uniform(3, 6))

                    job_cards = await page.query_selector_all(".job_seen_beacon")
                    count = 0
                    for card in job_cards:
                        if count >= MAX_JOBS_PER_QUERY:
                            break
                        try:
                            title_el = await card.query_selector("[data-testid='jobTitle']")
                            company_el = await card.query_selector("[data-testid='company-name']")
                            location_el = await card.query_selector("[data-testid='text-location']")
                            a_el = await card.query_selector("a[data-jk]")

                            jk = await a_el.get_attribute("data-jk") if a_el else None
                            if not jk:
                                continue
                            href = f"https://www.indeed.com/viewjob?jk={jk}"
                            if href in jobs:
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
