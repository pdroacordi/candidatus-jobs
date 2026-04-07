import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models import JobSource


class JobOut(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    location: str | None
    remote: bool
    description: str
    url: str
    source: JobSource
    required_skills: list[str]
    job_level: str | None
    posted_at: datetime | None
    scraped_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class JobRecommended(JobOut):
    match_score: float


class JobsPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[JobOut]
