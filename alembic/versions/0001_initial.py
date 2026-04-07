"""initial

Revision ID: 0001
Revises:
Create Date: 2026-04-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("remote", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False, unique=True),
        sa.Column(
            "source",
            sa.Enum("linkedin", "indeed", "gupy", "remotive", "arbeitnow", name="jobsource"),
            nullable=False,
        ),
        sa.Column("required_skills", ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("job_level", sa.String(50), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_jobs_is_active", "jobs", ["is_active"])
    op.create_index("ix_jobs_scraped_at", "jobs", ["scraped_at"])
    op.create_index("ix_jobs_source", "jobs", ["source"])


def downgrade() -> None:
    op.drop_table("jobs")
    op.execute("DROP TYPE IF EXISTS jobsource")
