# Job Ranking & Recommendation API — Project Plan

## Problem Statement

Given a user's profile (skills, experience, preferences), surface the most
relevant job listings from a pool, sorted by a weighted match score. The goal
is a working prototype that can evolve into a production recommendation system.

---

## Architecture

```
Client
  │
  ▼
FastAPI (app/main.py)
  │   CORSMiddleware
  │   APITraceMiddleware   ← injects X-Trace-Id, logs every request
  │   AuthMiddleware       ← route-group guards (public / private / admin / internal)
  │
  ▼
Routers  (app/routers/)
  │   /api/v1/public/users          → user_profile.py
  │   /api/v1/public/jobs           → job.py
  │   /api/v1/public/recommendations → recommendation.py
  │   /api/v1/health
  │
  ▼
Controllers  (app/controller/)
  │   UserProfileController
  │   JobController
  │   RecommendationController  ← orchestrates user fetch + job fetch + ranker
  │
  ▼
DB Services  (app/db/services/)          Ranker  (app/ranker.py)
  │   UserProfileDB(BaseDB[UserProfileModel])       pure function, no I/O
  │   JobDB(BaseDB[JobModel])
  │
  ▼
SQLAlchemy ORM  (app/db/models/)
  │   UserProfileModel  →  table: user_profiles
  │   JobModel          →  table: jobs
  │
  ▼
PostgreSQL  (docker-compose-local-db.yaml)
```

---

## Data Models

### `user_profiles`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | gen_random_uuid() |
| name | VARCHAR(255) | |
| email | VARCHAR(255) | UNIQUE |
| skills | TEXT[] | e.g. `["python", "fastapi"]` |
| experience_years | INTEGER | |
| preferred_roles | TEXT[] | e.g. `["backend engineer"]` |
| location | VARCHAR(255) | city name or empty |
| remote_ok | BOOLEAN | |
| salary_min | INTEGER | USD/year |

### `jobs`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | gen_random_uuid() |
| title | VARCHAR(255) | |
| company | VARCHAR(255) | |
| required_skills | TEXT[] | |
| experience_min | INTEGER | years |
| location | VARCHAR(255) | |
| remote | BOOLEAN | |
| salary | INTEGER | USD/year |
| description | TEXT | |
| is_active | BOOLEAN | default true |

---

## Ranking Algorithm

Five weighted dimensions, each normalised to 0–1:

| Dimension | Weight | Logic |
|---|---|---|
| Skills match | **0.45** | `len(user ∩ job skills) / len(job skills)` |
| Role match | **0.20** | Any preferred_role substring found in job title |
| Experience fit | **0.15** | 1.0 if user ≥ min; 0.0 if under; slight decay if 5+ yrs over |
| Location/remote | **0.10** | 1.0 if remote match OR exact city match |
| Salary fit | **0.10** | 1.0 if job salary ≥ user minimum |

`final_score = Σ (sub_score × weight)` — jobs sorted descending.

Each `RankedJob` response includes `match_reasons` so the score is explainable.

---

## API Reference

Base prefix: `/api/v1/public`

| Method | Path | Description |
|---|---|---|
| POST | `/users` | Create a user profile |
| GET | `/users/{user_id}` | Fetch a user profile |
| POST | `/jobs` | Add a job listing |
| GET | `/jobs` | List all active jobs |
| GET | `/recommendations/{user_id}` | Get ranked job recommendations |
| GET | `/health` | Health check |

---

## Local Dev Setup

```bash
# 1. Clone & enter
git clone git@github.com:hardik-shukla-99/cc-job-ranking.git
cd cc-job-ranking

# 2. Copy env and fill in DB creds (defaults work with docker-compose)
cp .env.example .env

# 3. Start Postgres
docker-compose -f docker-compose-local-db.yaml up -d

# 4. Install dependencies
poetry install

# 5. Generate & run migration
poetry run alembic revision --autogenerate -m "init"
poetry run alembic upgrade head

# 6. Seed sample jobs
poetry run python scripts/seed.py

# 7. Run the API
poetry run uvicorn app.main:app --reload
# → http://127.0.0.1:8000/docs
```

---

## Adding a New Feature

1. `app/db/models/<name>.py` — SQLAlchemy ORM model (subclass `Base`)
2. `app/db/services/<name>.py` — `class FooDB(BaseDB[FooModel])`
3. `app/controller/<name>.py` — business logic, calls DB service
4. `app/routers/<name>.py` — APIRouter, calls controller
5. Wire router in `app/routers/__init__.py` under the appropriate route group
6. Export model from `app/db/models/__init__.py` so Alembic sees it
7. `poetry run alembic revision --autogenerate -m "add foo table"`
8. `poetry run alembic upgrade head`

---

## What's Deferred (Post-Prototype)

- Auth / JWT validation in `AuthMiddleware`
- Pagination & filtering on `/jobs`
- Embeddings-based semantic skill matching (cosine similarity)
- Async job ingestion from LinkedIn / Indeed APIs
- User feedback loop (thumbs up/down to re-weight scores)
- Background re-ranking with Celery + Redis
