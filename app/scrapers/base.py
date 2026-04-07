from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawJob:
    title: str
    company: str
    description: str
    url: str
    location: str | None = None
    remote: bool = False
    job_level: str | None = None
    posted_at: datetime | None = None


class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self) -> list[RawJob]:
        """Fetch and return raw job listings from the source."""
        ...

