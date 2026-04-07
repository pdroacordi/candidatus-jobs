"""Simple skill-intersection match scorer."""
from app.models import Job


def compute_match_score(job: Job, user_skills: list[str]) -> float:
    """
    Returns a score in [0, 1].
    score = |user_skills ∩ job.required_skills| / |job.required_skills|
    Jobs with fewer than 3 extracted skills are penalised to avoid
    false high scores from sparse descriptions.
    """
    if not job.required_skills or len(job.required_skills) < 3:
        return 0.0
    user_set = {s.lower() for s in user_skills}
    job_set = {s.lower() for s in job.required_skills}
    intersection = user_set & job_set
    return len(intersection) / len(job_set)
