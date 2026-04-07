"""Keyword-based skill extraction from job descriptions."""

TECH_SKILLS = {
    # Languages
    "python", "javascript", "typescript", "java", "kotlin", "swift", "go", "golang",
    "rust", "c++", "c#", "ruby", "php", "scala", "r", "dart", "elixir",
    # Frontend
    "react", "vue", "angular", "next.js", "nextjs", "nuxt", "svelte", "html", "css",
    "tailwindcss", "tailwind", "sass", "webpack", "vite", "redux", "zustand",
    # Backend
    "node.js", "nodejs", "fastapi", "django", "flask", "spring", "express", "nestjs",
    "rails", "laravel", "graphql", "rest", "grpc",
    # Databases
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "supabase", "firebase", "prisma", "sqlalchemy",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", "terraform",
    "ansible", "ci/cd", "github actions", "jenkins", "linux",
    # Data & AI
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "pandas", "numpy", "spark", "airflow", "dbt", "kafka", "data engineering",
    "llm", "openai", "langchain",
    # Mobile
    "react native", "flutter", "android", "ios", "expo",
    # Tools & Practices
    "git", "agile", "scrum", "tdd", "microservices", "monorepo",
}


def extract_skills(text: str) -> list[str]:
    """Return tech skills found in the given text (case-insensitive)."""
    text_lower = text.lower()
    found = []
    for skill in TECH_SKILLS:
        # Match whole-word-ish — skill surrounded by non-alphanumeric chars or boundaries
        import re
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(found)
