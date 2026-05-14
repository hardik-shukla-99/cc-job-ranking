"""Seed the database with realistic job listings."""
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1/public"

JOBS = [
    {
        "title": "Senior Backend Engineer",
        "company": "Stripe",
        "required_skills": ["python", "go", "postgresql", "redis", "docker"],
        "experience_min": 5,
        "location": "San Francisco",
        "remote": True,
        "salary": 200000,
        "description": "Build and scale payment infrastructure.",
    },
    {
        "title": "Backend Engineer",
        "company": "Notion",
        "required_skills": ["python", "fastapi", "postgresql", "aws"],
        "experience_min": 3,
        "location": "San Francisco",
        "remote": True,
        "salary": 160000,
        "description": "Build APIs for the Notion platform.",
    },
    {
        "title": "Data Engineer",
        "company": "Databricks",
        "required_skills": ["python", "spark", "sql", "airflow", "aws"],
        "experience_min": 3,
        "location": "Seattle",
        "remote": True,
        "salary": 175000,
        "description": "Design and maintain data pipelines.",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "OpenAI",
        "required_skills": ["python", "pytorch", "cuda", "transformers", "docker"],
        "experience_min": 4,
        "location": "San Francisco",
        "remote": False,
        "salary": 250000,
        "description": "Train and deploy large language models.",
    },
    {
        "title": "Full Stack Engineer",
        "company": "Linear",
        "required_skills": ["typescript", "react", "node", "postgresql", "graphql"],
        "experience_min": 3,
        "location": "Remote",
        "remote": True,
        "salary": 150000,
        "description": "Build product features end-to-end.",
    },
    {
        "title": "DevOps Engineer",
        "company": "HashiCorp",
        "required_skills": ["terraform", "kubernetes", "docker", "aws", "python"],
        "experience_min": 4,
        "location": "Remote",
        "remote": True,
        "salary": 170000,
        "description": "Own infrastructure automation and reliability.",
    },
    {
        "title": "Python Developer",
        "company": "Weights & Biases",
        "required_skills": ["python", "fastapi", "docker", "postgresql"],
        "experience_min": 2,
        "location": "San Francisco",
        "remote": True,
        "salary": 140000,
        "description": "Develop tooling for ML experiment tracking.",
    },
    {
        "title": "Software Engineer — Platform",
        "company": "Vercel",
        "required_skills": ["node", "typescript", "aws", "docker", "redis"],
        "experience_min": 3,
        "location": "Remote",
        "remote": True,
        "salary": 155000,
        "description": "Build the edge deployment platform.",
    },
    {
        "title": "Junior Backend Developer",
        "company": "Startups Inc.",
        "required_skills": ["python", "fastapi", "sql"],
        "experience_min": 0,
        "location": "New York",
        "remote": False,
        "salary": 95000,
        "description": "Entry-level backend role.",
    },
    {
        "title": "Data Scientist",
        "company": "Spotify",
        "required_skills": ["python", "sql", "scikit-learn", "spark", "statistics"],
        "experience_min": 2,
        "location": "New York",
        "remote": True,
        "salary": 145000,
        "description": "Analyse user behaviour to improve recommendations.",
    },
    {
        "title": "Site Reliability Engineer",
        "company": "Cloudflare",
        "required_skills": ["kubernetes", "python", "go", "prometheus", "aws"],
        "experience_min": 4,
        "location": "Austin",
        "remote": True,
        "salary": 180000,
        "description": "Keep the global network running at scale.",
    },
    {
        "title": "API Engineer",
        "company": "Twilio",
        "required_skills": ["python", "fastapi", "redis", "postgresql", "docker"],
        "experience_min": 2,
        "location": "Remote",
        "remote": True,
        "salary": 130000,
        "description": "Design developer-facing communication APIs.",
    },
]


def seed() -> None:
    with httpx.Client(timeout=10) as client:
        for job in JOBS:
            resp = client.post(f"{BASE_URL}/jobs", json=job)
            resp.raise_for_status()
            print(f"Seeded: {job['title']} @ {job['company']}")
    print(f"\nDone — {len(JOBS)} jobs inserted.")


if __name__ == "__main__":
    seed()
