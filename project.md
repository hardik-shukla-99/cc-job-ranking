# cc-job-ranking — Project Documentation

## Overview

A FastAPI-based prototype that ranks and recommends job listings to users based
on a weighted match score derived from their profile (skills, experience,
preferences, location, salary expectations).

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.112+ |
| Language | Python 3.12 |
| ORM | SQLAlchemy 2.0 (declarative mapped columns) |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Config | pydantic-settings + `.env` |
| Testing | pytest + unittest.mock + FastAPI TestClient |
| Local DB | Docker Compose |
| Dependency mgmt | Poetry |

---

## Architecture

```
Client (HTTP)
    │
    ▼
FastAPI app  (app/main.py)
    │  CORSMiddleware
    │  APITraceMiddleware   ← injects X-Trace-Id, logs every request with duration
    │  AuthMiddleware       ← guards /private, /admin, /internal route groups
    │
    ▼
Routers  (app/routers/)
    ├── /api/v1/public/users            → routers/user_profile.py
    ├── /api/v1/public/jobs             → routers/job.py
    ├── /api/v1/public/recommendations  → routers/recommendation.py
    └── /api/v1/health                  → routers/health.py
    │
    ▼
Controllers  (app/controller/)
    ├── UserProfileController   — duplicate check, 404 guard
    ├── JobController           — pass-through to DB service
    └── RecommendationController — orchestrates user + jobs fetch → ranker
    │
    ▼
DB Services  (app/db/services/)          Ranker  (app/ranker.py)
    ├── UserProfileDB(BaseDB[...])  ←——   pure function, no I/O
    └── JobDB(BaseDB[...])
              │
              ▼
        SQLAlchemy ORM  (app/db/models/)
              ├── UserProfileModel  →  table: user_profiles
              └── JobModel          →  table: jobs
                        │
                        ▼
                   PostgreSQL
```

### Route Groups

All routes live under `/api/v1/`. The group prefix is enforced by
`AuthMiddleware`:

| Prefix | Auth | Purpose |
|---|---|---|
| `/public/` | None | Open endpoints (this prototype uses public only) |
| `/private/` | Bearer JWT | Authenticated user actions |
| `/admin/` | Bearer JWT + admin role | Admin actions |
| `/internal/` | `INTERNAL_TOKEN` header | Service-to-service calls |

---

## Data Models

### `user_profiles` table

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | Unique user ID |
| `name` | VARCHAR(255) | NOT NULL | Display name |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Used for dedup check on create |
| `skills` | TEXT[] | NOT NULL | e.g. `["python", "fastapi", "sql"]` |
| `experience_years` | INTEGER | NOT NULL, default 0 | Total years of work experience |
| `preferred_roles` | TEXT[] | NOT NULL | e.g. `["backend engineer"]` |
| `location` | VARCHAR(255) | NOT NULL | City name or empty string |
| `remote_ok` | BOOLEAN | NOT NULL | Whether user accepts remote jobs |
| `salary_min` | INTEGER | NOT NULL | Minimum acceptable salary (USD/yr) |

### `jobs` table

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | Unique job ID |
| `title` | VARCHAR(255) | NOT NULL | e.g. "Senior Backend Engineer" |
| `company` | VARCHAR(255) | NOT NULL | Hiring company |
| `required_skills` | TEXT[] | NOT NULL | Skills the role requires |
| `experience_min` | INTEGER | NOT NULL | Minimum years required |
| `location` | VARCHAR(255) | NOT NULL | City or "Remote" |
| `remote` | BOOLEAN | NOT NULL | Whether the role is remote |
| `salary` | INTEGER | NOT NULL | Offered salary (USD/yr) |
| `description` | TEXT | NOT NULL | Role description |
| `is_active` | BOOLEAN | NOT NULL, default true | Soft-delete flag |

---

## Ranking Algorithm

Five weighted dimensions, each normalised to 0.0–1.0:

```
final_score = (skills × 0.45) + (role × 0.20) + (experience × 0.15)
            + (location × 0.10) + (salary × 0.10)
```

| Dimension | Weight | Scoring Logic |
|---|---|---|
| **Skills** | 0.45 | `len(user_skills ∩ job_skills) / len(job_skills)` — case-insensitive set intersection |
| **Role** | 0.20 | 1.0 if any `preferred_role` is a substring of the job title, else 0 |
| **Experience** | 0.15 | 1.0 if `user.years ≥ job.exp_min`; 0 if under; decays by 0.05/yr beyond +5yr gap (floor 0.5) |
| **Location** | 0.10 | 1.0 if (job is remote AND user `remote_ok`) OR city names match exactly (case-insensitive) |
| **Salary** | 0.10 | 1.0 if `job.salary ≥ user.salary_min`, else 0 |

Each `RankedJob` in the response carries a `match_reasons` list (one human-readable string per dimension) so the score is fully explainable.

---

## API Reference

Base URL: `http://localhost:8000/api/v1/public`

### Users

#### `POST /users`
Create a new user profile.

**Request body:**
```json
{
  "name": "Hardik Shukla",
  "email": "hardik@example.com",
  "skills": ["python", "fastapi", "postgresql"],
  "experience_years": 4,
  "preferred_roles": ["backend engineer"],
  "location": "San Francisco",
  "remote_ok": true,
  "salary_min": 130000
}
```

**Responses:** `201 Created` / `409 Conflict` (duplicate email) / `422 Unprocessable Entity`

---

#### `GET /users/{user_id}`
Fetch a user profile by UUID.

**Responses:** `200 OK` / `404 Not Found` / `422 Unprocessable Entity`

---

### Jobs

#### `POST /jobs`
Add a job listing.

**Request body:**
```json
{
  "title": "Senior Backend Engineer",
  "company": "Stripe",
  "required_skills": ["python", "go", "postgresql"],
  "experience_min": 5,
  "location": "San Francisco",
  "remote": true,
  "salary": 200000,
  "description": "Build payment infrastructure."
}
```

**Responses:** `201 Created` / `422 Unprocessable Entity`

---

#### `GET /jobs`
List all active job listings.

**Responses:** `200 OK` (may be empty array)

---

### Recommendations

#### `GET /recommendations/{user_id}`
Return all active jobs ranked by match score for the given user.

**Response (200):**
```json
{
  "status": 200,
  "message": "Recommendations retrieved",
  "payload": {
    "user_id": "b5316cd9-...",
    "ranked_jobs": [
      {
        "job": { "id": "...", "title": "Backend Engineer", ... },
        "score": 0.8875,
        "match_reasons": [
          "Skills matched: fastapi, postgresql, python (3/4)",
          "Role 'backend engineer' matches job title",
          "Experience fit (4y, min 3y)",
          "Remote position matches preference",
          "Salary $160,000 meets minimum $130,000"
        ]
      }
    ]
  }
}
```

**Responses:** `200 OK` / `404 Not Found` / `422 Unprocessable Entity`

---

### Health

#### `GET /health`
Liveness check.

**Response (200):** `{"status": 200, "message": "OK", "payload": null}`

---

## Project Structure

```
cc-job-ranking/
├── app/
│   ├── main.py                         FastAPI app, middleware, startup
│   ├── ranker.py                       Pure scoring/ranking function
│   ├── constants/                      Shared constants + RouteType enum
│   ├── core/                           Config, custom exceptions, logging
│   ├── db/
│   │   ├── client.py                   DBClient (engine, session factory)
│   │   ├── migrate.py                  Alembic runner called on startup
│   │   ├── models/                     SQLAlchemy ORM models
│   │   └── services/                   BaseDB[T] + domain DB services
│   ├── middlewares/                    APITraceMiddleware, AuthMiddleware
│   ├── models/                         Pydantic request/response schemas
│   ├── routers/                        FastAPI routers (one per domain)
│   └── controller/                     Business logic layer
├── migrations/                         Alembic migration scripts
├── scripts/seed.py                     Seeds 12 realistic jobs via API
├── tests/                              Pytest test suite (82 tests)
├── docker-compose-local-db.yaml
├── pyproject.toml
└── .env.example
```

---

## Local Development

```bash
# 1. Clone
git clone git@github.com:hardik-shukla-99/cc-job-ranking.git && cd cc-job-ranking

# 2. Environment
cp .env.example .env

# 3. Start Postgres
sudo docker compose -f docker-compose-local-db.yaml up -d

# 4. Install dependencies
poetry install

# 5. Migrate
poetry run alembic revision --autogenerate -m "init"
poetry run alembic upgrade head

# 6. Seed sample data
poetry run python scripts/seed.py

# 7. Run
poetry run uvicorn app.main:app --reload
# → http://127.0.0.1:8000/docs
```

---

## Testing

```bash
poetry run pytest tests/ -v                    # run all 82 tests
poetry run pytest tests/test_ranker.py -v      # ranker unit tests only
poetry run pytest tests/test_api_users.py -v   # user API tests only
poetry run pytest tests/ --cov=app             # with coverage
```

Tests run **without a database** — startup is patched, DB sessions are mocked,
and controller methods are patched per test class.

---

## Adding a New Feature

1. `app/db/models/<name>.py` — SQLAlchemy ORM model (`Base` subclass)
2. `app/db/services/<name>.py` — `class FooDB(BaseDB[FooModel])`
3. `app/controller/<name>.py` — business logic, raises `HTTPException` for errors
4. `app/routers/<name>.py` — `APIRouter`, calls controller, returns `BaseResponse[T]`
5. Wire router in `app/routers/__init__.py` under the appropriate route group
6. Export model in `app/db/models/__init__.py` so Alembic sees it
7. `poetry run alembic revision --autogenerate -m "add foo"`
8. `poetry run alembic upgrade head`
9. Add tests: `tests/test_api_<name>.py` + `tests/test_controllers.py`

---

## What's Deferred

- JWT auth in `AuthMiddleware` (skeleton is wired, just needs `verify_token`)
- Pagination (`?page=` / `?limit=`) on `GET /jobs`
- Embeddings-based semantic skill matching (cosine similarity with sentence-transformers)
- User feedback loop (thumbs up/down to personalise score weights)
- Async job ingestion from LinkedIn / Indeed APIs
- Background re-ranking with Celery + Redis
- Rate limiting
