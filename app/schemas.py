import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models import JobSource


class JobOut(BaseModel):
    id: uuid.UUID = Field(description="Unique job identifier")
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str | None = Field(None, description="Office location, if specified")
    remote: bool = Field(description="Whether the position is remote-friendly")
    description: str = Field(description="Full job description")
    url: str = Field(description="Original job listing URL")
    source: JobSource = Field(description="Platform where the job was scraped from")
    required_skills: list[str] = Field(description="Skills extracted from the description")
    job_level: str | None = Field(None, description="Seniority level (e.g. junior, senior)")
    posted_at: datetime | None = Field(None, description="When the job was originally posted")
    scraped_at: datetime = Field(description="When the job was ingested by this system")
    is_active: bool = Field(description="False when the listing has been marked stale")

    model_config = {"from_attributes": True}


class JobRecommended(JobOut):
    match_score: float = Field(description="Similarity score between 0 and 1 against the requested skills")


class JobsPage(BaseModel):
    total: int = Field(description="Total number of jobs matching the filters")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    items: list[JobOut] = Field(description="Jobs on this page")
