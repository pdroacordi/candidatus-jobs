import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class JobSource(str, enum.Enum):
    linkedin = "linkedin"
    indeed = "indeed"
    gupy = "gupy"
    remotive = "remotive"
    arbeitnow = "arbeitnow"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1024), unique=True)
    source: Mapped[JobSource] = mapped_column(SAEnum(JobSource))
    required_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    job_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
