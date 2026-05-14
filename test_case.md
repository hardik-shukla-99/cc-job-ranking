# Test Cases — cc-job-ranking

**Suite:** 82 tests | **Run:** `poetry run pytest tests/ -v` | **DB required:** No

Test IDs use the format `<module>/<class>/<method>`.

---

## 1. Ranker Unit Tests (`tests/test_ranker.py`)

No DB, no HTTP. Tests the pure scoring functions and the `rank_jobs` orchestrator.

### 1.1 Skills Score (`TestSkillsScore`)

| # | Test | Input | Expected |
|---|---|---|---|
| R-SK-01 | Full skill match | user=`[python, fastapi]`, job=`[python, fastapi]` | score = 1.0 |
| R-SK-02 | Partial match | user=`[python, fastapi, go]`, job=`[python, go, rust]` | score ≈ 0.667 |
| R-SK-03 | No overlap | user=`[python]`, job=`[swift, kotlin]` | score = 0.0 |
| R-SK-04 | Job has no required skills | user=any, job=`[]` | score = 1.0, reason contains "No specific skills required" |
| R-SK-05 | Case-insensitive matching | user=`[Python, FastAPI]`, job=`[python, fastapi]` | score = 1.0 |
| R-SK-06 | Reason lists matched skills | user=`[python, go]`, job=`[python, go, rust]` | reason contains "python" and "go" |
| R-SK-07 | Empty user skills | user=`[]`, job=`[python, fastapi]` | score = 0.0 |

### 1.2 Role Score (`TestRoleScore`)

| # | Test | Input | Expected |
|---|---|---|---|
| R-RO-01 | Exact role substring | roles=`[backend engineer]`, title="Senior Backend Engineer" | score = 1.0 |
| R-RO-02 | Partial title match | roles=`[engineer]`, title="Software Engineer — Platform" | score = 1.0 |
| R-RO-03 | No match | roles=`[backend engineer]`, title="iOS Developer" | score = 0.0, reason "not matched" |
| R-RO-04 | Case-insensitive | roles=`[DATA ENGINEER]`, title="Data Engineer" | score = 1.0 |
| R-RO-05 | First matching role wins | roles=`[backend, frontend]`, title="Backend Engineer" | score = 1.0, reason contains "backend" |
| R-RO-06 | Empty preferred roles | roles=`[]`, title=any | score = 0.0 |

### 1.3 Experience Score (`TestExperienceScore`)

| # | Test | Input (user_yrs, min) | Expected |
|---|---|---|---|
| R-EX-01 | Exactly meets minimum | 3, 3 | score = 1.0 |
| R-EX-02 | Exceeds minimum | 5, 3 | score = 1.0 |
| R-EX-03 | Below minimum | 1, 5 | score = 0.0, reason "Under-experienced" |
| R-EX-04 | Heavily over-qualified decays | gap 5 vs gap 15 | score(gap=15) ≤ score(gap=5) |
| R-EX-05 | Decay floor at 0.5 | 100, 0 | score ≥ 0.5 |
| R-EX-06 | Zero minimum | 0, 0 | score = 1.0 |

### 1.4 Location Score (`TestLocationScore`)

| # | Test | Input | Expected |
|---|---|---|---|
| R-LO-01 | Remote job + remote_ok user | remote=True, remote_ok=True | score = 1.0, "Remote position" in reason |
| R-LO-02 | Exact city match | both "San Francisco", remote=False | score = 1.0, city in reason |
| R-LO-03 | City mismatch, not remote | "New York" vs "Austin" | score = 0.0, "mismatch" in reason |
| R-LO-04 | Remote job, user not ok with remote | remote_ok=False | falls back to city; city mismatch → 0.0 |
| R-LO-05 | Case-insensitive city | "san francisco" vs "San Francisco" | score = 1.0 |
| R-LO-06 | Empty user location | user.location="" | score = 0.0 (prevents false city match) |

### 1.5 Salary Score (`TestSalaryScore`)

| # | Test | Input (min, offered) | Expected |
|---|---|---|---|
| R-SA-01 | Salary exceeds minimum | min=100k, offered=120k | score = 1.0, "meets minimum" in reason |
| R-SA-02 | Salary exactly at minimum | min=100k, offered=100k | score = 1.0 |
| R-SA-03 | Salary below minimum | min=150k, offered=100k | score = 0.0, "below minimum" in reason |
| R-SA-04 | Zero minimum | min=0, offered=1 | score = 1.0 |

### 1.6 `rank_jobs` Orchestrator (`TestRankJobs`)

| # | Test | Scenario | Expected |
|---|---|---|---|
| R-RJ-01 | Empty job pool | jobs=`[]` | returns `[]` |
| R-RJ-02 | Results sorted descending | 5 random jobs | scores in descending order |
| R-RJ-03 | All scores in bounds | 5 jobs | 0.0 ≤ score ≤ 1.0 for all |
| R-RJ-04 | Perfect match ranks first | good job vs iOS developer | good job ranked #1, score difference > 0 |
| R-RJ-05 | Low salary pushed down | salary below vs above minimum | higher-salary job ranked first |
| R-RJ-06 | Under-experienced reason text | user.years=1, job.exp_min=5 | "Under-experienced" in match_reasons |
| R-RJ-07 | Remote preference wins | remote job vs onsite mismatch | remote job ranked first |
| R-RJ-08 | Always 5 match reasons | any valid job | len(match_reasons) == 5 |
| R-RJ-09 | Single job still ranked | jobs=[1 job] | len(result) == 1, score ≥ 0.0 |
| R-RJ-10 | No user skills → zero skills | user.skills=[], job needs skills | reason contains "0/" |

---

## 2. Controller Unit Tests (`tests/test_controllers.py`)

DB services are mocked with `unittest.mock.patch`. No DB or HTTP.

### 2.1 UserProfileController

| # | Test | Precondition | Expected |
|---|---|---|---|
| C-UP-01 | Create succeeds | `get_by_filter` → None (no duplicate) | returns created UserProfileModel |
| C-UP-02 | Create raises 409 on duplicate email | `get_by_filter` → existing user | raises `HTTPException(409)` |
| C-UP-03 | get_by_id returns user | `get_by_id` → mock user | returns same mock |
| C-UP-04 | get_by_id raises 404 | `get_by_id` → None | raises `HTTPException(404)` |
| C-UP-05 | 404 detail contains user ID | `get_by_id` → None | `exc.detail` contains the UUID string |

### 2.2 JobController

| # | Test | Precondition | Expected |
|---|---|---|---|
| C-JB-01 | Create returns job | `create` → mock job | returns same mock |
| C-JB-02 | list_active returns active jobs | `get_active_jobs` → [3 active] | returns all 3, all is_active=True |
| C-JB-03 | list_active returns empty | `get_active_jobs` → [] | returns `[]` |

### 2.3 RecommendationController

| # | Test | Precondition | Expected |
|---|---|---|---|
| C-RC-01 | Returns RecommendationResponse | user found, 1 active job | response.user_id matches, len(ranked_jobs)=1 |
| C-RC-02 | Propagates 404 for unknown user | `get_by_id` → None | raises `HTTPException(404)` |
| C-RC-03 | Empty jobs → empty ranked list | user found, jobs=[] | ranked_jobs=[] |
| C-RC-04 | Ranked jobs sorted by score | good job + bad job | ranked_jobs[0].score ≥ ranked_jobs[1].score |

---

## 3. User API Tests (`tests/test_api_users.py`)

Full HTTP stack via FastAPI `TestClient`. `UserProfileController` methods are patched.

### 3.1 POST `/api/v1/public/users`

| # | Test | Input | Mock | Expected HTTP |
|---|---|---|---|---|
| A-UP-01 | Valid payload → created | full valid body | `create` → mock user | 201, `payload.email` matches |
| A-UP-02 | Response contains UUID | valid body | `create` → mock user with UUID | 201, `payload.id` = UUID string |
| A-UP-03 | Duplicate email | valid body | `create` raises HTTPException(409) | 409 |
| A-UP-04 | Missing email field | body without email | — (pydantic validation) | 422 |
| A-UP-05 | Missing name field | body without name | — | 422 |
| A-UP-06 | Invalid email format | email="not-an-email" | — | 422 |
| A-UP-07 | Negative salary_min accepted | salary_min=-1 | `create` → mock | 201 |
| A-UP-08 | Empty skills list accepted | skills=[] | `create` → mock | 201 |

### 3.2 GET `/api/v1/public/users/{user_id}`

| # | Test | Input | Mock | Expected HTTP |
|---|---|---|---|---|
| A-UP-09 | Valid UUID, user found | real UUID | `get_by_id` → mock user | 200, `payload.id` matches |
| A-UP-10 | Valid UUID, user missing | real UUID | `get_by_id` raises HTTPException(404) | 404 |
| A-UP-11 | Non-UUID path param | "not-a-uuid" | — | 422 |
| A-UP-12 | Response contains all fields | real UUID | `get_by_id` → mock | 200, all 9 fields present in payload |

---

## 4. Job API Tests (`tests/test_api_jobs.py`)

Full HTTP stack. `JobController` methods are patched.

### 4.1 POST `/api/v1/public/jobs`

| # | Test | Input | Mock | Expected HTTP |
|---|---|---|---|---|
| A-JB-01 | Valid payload → created | full valid body | `create` → mock job | 201, status=201 |
| A-JB-02 | Response contains job fields | valid body | `create` → mock with UUID | 201, `id`, `title`, `company` in payload |
| A-JB-03 | Missing title → 422 | body without title | — | 422 |
| A-JB-04 | Missing company → 422 | body without company | — | 422 |
| A-JB-05 | Empty skills accepted | skills=[] | `create` → mock | 201 |
| A-JB-06 | Zero salary accepted | salary=0 | `create` → mock | 201 |

### 4.2 GET `/api/v1/public/jobs`

| # | Test | Mock | Expected |
|---|---|---|---|
| A-JB-07 | Returns list of jobs | `list_active` → [3 mocks] | 200, `len(payload)` = 3 |
| A-JB-08 | Empty list when no jobs | `list_active` → [] | 200, `payload` = [] |
| A-JB-09 | Each job has required fields | `list_active` → [1 mock] | all 9 fields present in job object |
| A-JB-10 | Only active jobs in response | `list_active` → [2 active] | all `is_active=true` |

---

## 5. Recommendation API Tests (`tests/test_api_recommendations.py`)

Full HTTP stack. `RecommendationController.get_recommendations` is patched.

### GET `/api/v1/public/recommendations/{user_id}`

| # | Test | Mock | Expected |
|---|---|---|---|
| A-RC-01 | Valid user → 200 | returns RecommendationResponse | 200 |
| A-RC-02 | Response contains user_id | RecommendationResponse with UUID | `payload.user_id` matches |
| A-RC-03 | Response has ranked_jobs list | response with 3 ranked jobs | `len(payload.ranked_jobs)` = 3 |
| A-RC-04 | Each job has score and reasons | 1 ranked job | `score` and `match_reasons` (list) present |
| A-RC-05 | Jobs sorted by score descending | 4 ranked jobs with descending scores | scores in descending order |
| A-RC-06 | Unknown user → 404 | raises HTTPException(404) | 404 |
| A-RC-07 | Non-UUID path param → 422 | — | 422 |
| A-RC-08 | Empty job pool → empty list | ranked_jobs=[] | `payload.ranked_jobs` = [] |
| A-RC-09 | Each ranked job has full job details | 1 ranked job | `id`, `title`, `company`, `salary`, `remote`, `location` present |

---

## Coverage Summary

| Layer | File(s) | Tests | Type |
|---|---|---|---|
| Ranking engine | `app/ranker.py` | 39 | Unit |
| Controllers | `app/controller/*.py` | 12 | Unit (mocked services) |
| Users API | `app/routers/user_profile.py` | 12 | Integration (mocked controller) |
| Jobs API | `app/routers/job.py` | 10 | Integration (mocked controller) |
| Recommendations API | `app/routers/recommendation.py` | 9 | Integration (mocked controller) |
| **Total** | | **82** | |

---

## Running Tests

```bash
# All tests
poetry run pytest tests/ -v

# Specific module
poetry run pytest tests/test_ranker.py -v
poetry run pytest tests/test_controllers.py -v
poetry run pytest tests/test_api_users.py -v
poetry run pytest tests/test_api_jobs.py -v
poetry run pytest tests/test_api_recommendations.py -v

# With coverage report
poetry run pytest tests/ --cov=app --cov-report=term-missing

# Stop on first failure
poetry run pytest tests/ -x
```

> Tests run without a live database. `conftest.py` patches `_init_resources`
> (startup) and overrides the `DBClient.get_db_session` dependency with a
> `MagicMock`. Individual tests patch controller methods as needed.
