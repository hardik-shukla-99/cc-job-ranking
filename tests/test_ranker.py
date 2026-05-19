"""Unit tests for the ranking engine — no DB, no HTTP."""
import uuid
from unittest.mock import MagicMock

import pytest

from app.db.models.job import JobModel
from app.db.models.user_profile import UserProfileModel
from app.db.services.ranking import (
    RankingService,
    _experience_score,
    _location_score,
    _role_score,
    _salary_score,
    _skills_score,
)

rank_jobs = RankingService().rank_jobs


# ── helpers ──────────────────────────────────────────────────────────────────

def _user(**kwargs: object) -> UserProfileModel:
    defaults = dict(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        skills=["python", "fastapi", "postgresql"],
        experience_years=4,
        preferred_roles=["backend engineer"],
        location="San Francisco",
        remote_ok=True,
        salary_min=120000,
    )
    defaults.update(kwargs)
    m = MagicMock(spec=UserProfileModel)
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


def _job(**kwargs: object) -> JobModel:
    defaults = dict(
        id=uuid.uuid4(),
        title="Backend Engineer",
        company="ACME",
        required_skills=["python", "fastapi"],
        experience_min=3,
        location="San Francisco",
        remote=True,
        salary=150000,
        description="",
        is_active=True,
    )
    defaults.update(kwargs)
    m = MagicMock(spec=JobModel)
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


# ── _skills_score ─────────────────────────────────────────────────────────────

class TestSkillsScore:
    def test_full_match_returns_one(self) -> None:
        score, _ = _skills_score(["python", "fastapi"], ["python", "fastapi"])
        assert score == 1.0

    def test_partial_match_returns_ratio(self) -> None:
        score, _ = _skills_score(["python", "fastapi", "go"], ["python", "go", "rust"])
        assert score == pytest.approx(2 / 3)

    def test_no_match_returns_zero(self) -> None:
        score, _ = _skills_score(["python"], ["swift", "kotlin"])
        assert score == 0.0

    def test_empty_job_skills_returns_one(self) -> None:
        score, reason = _skills_score(["python"], [])
        assert score == 1.0
        assert "No specific skills required" in reason

    def test_case_insensitive_matching(self) -> None:
        score, _ = _skills_score(["Python", "FastAPI"], ["python", "fastapi"])
        assert score == 1.0

    def test_reason_lists_matched_skills(self) -> None:
        _, reason = _skills_score(["python", "go"], ["python", "go", "rust"])
        assert "python" in reason
        assert "go" in reason

    def test_empty_user_skills_returns_zero(self) -> None:
        score, _ = _skills_score([], ["python", "fastapi"])
        assert score == 0.0

    def test_both_skills_empty_returns_one(self) -> None:
        score, reason = _skills_score([], [])
        assert score == 1.0
        assert "No specific skills required" in reason


# ── _role_score ───────────────────────────────────────────────────────────────

class TestRoleScore:
    def test_exact_role_match(self) -> None:
        score, reason = _role_score(["backend engineer"], "Senior Backend Engineer")
        assert score == 1.0
        assert "backend engineer" in reason.lower()

    def test_partial_title_match(self) -> None:
        score, _ = _role_score(["engineer"], "Software Engineer — Platform")
        assert score == 1.0

    def test_no_role_match(self) -> None:
        score, reason = _role_score(["backend engineer"], "iOS Developer")
        assert score == 0.0
        assert "not matched" in reason.lower()

    def test_case_insensitive(self) -> None:
        score, _ = _role_score(["DATA ENGINEER"], "Data Engineer")
        assert score == 1.0

    def test_first_matching_role_wins(self) -> None:
        score, reason = _role_score(["backend", "frontend"], "Backend Engineer")
        assert score == 1.0
        assert "backend" in reason.lower()

    def test_empty_preferred_roles_returns_zero(self) -> None:
        score, _ = _role_score([], "Backend Engineer")
        assert score == 0.0


# ── _experience_score ─────────────────────────────────────────────────────────

class TestExperienceScore:
    def test_exactly_meets_minimum_returns_one(self) -> None:
        score, _ = _experience_score(3, 3)
        assert score == 1.0

    def test_exceeds_minimum_returns_one(self) -> None:
        score, _ = _experience_score(5, 3)
        assert score == 1.0

    def test_below_minimum_returns_zero(self) -> None:
        score, reason = _experience_score(1, 5)
        assert score == 0.0
        assert "Under-experienced" in reason

    def test_heavily_over_qualified_decays(self) -> None:
        # gap = 15 - 0 = 15, which is > 5, so decay applies
        score_near, _ = _experience_score(5, 0)    # gap=5, no decay
        score_far, _ = _experience_score(15, 0)   # gap=15, decayed
        assert score_near >= score_far

    def test_decay_never_below_half(self) -> None:
        # Extreme over-qualification
        score, _ = _experience_score(100, 0)
        assert score >= 0.5

    def test_zero_min_experience_returns_one(self) -> None:
        score, _ = _experience_score(0, 0)
        assert score == 1.0


# ── _location_score ───────────────────────────────────────────────────────────

class TestLocationScore:
    def test_remote_job_and_remote_ok_user_returns_one(self) -> None:
        score, reason = _location_score("Tokyo", True, "Remote", True)
        assert score == 1.0
        assert "Remote" in reason

    def test_exact_city_match_returns_one(self) -> None:
        score, reason = _location_score("San Francisco", False, "San Francisco", False)
        assert score == 1.0
        assert "San Francisco" in reason

    def test_city_mismatch_and_not_remote_returns_zero(self) -> None:
        score, reason = _location_score("New York", False, "Austin", False)
        assert score == 0.0
        assert "mismatch" in reason.lower()

    def test_remote_job_but_user_not_ok_with_remote_falls_back_to_city(self) -> None:
        # job is remote but user doesn't want remote; city also doesn't match → 0
        score, _ = _location_score("New York", False, "Remote", True)
        assert score == 0.0

    def test_case_insensitive_city_match(self) -> None:
        score, _ = _location_score("san francisco", False, "San Francisco", False)
        assert score == 1.0

    def test_empty_user_location_prevents_city_match(self) -> None:
        score, _ = _location_score("", False, "", False)
        assert score == 0.0


# ── _salary_score ─────────────────────────────────────────────────────────────

class TestSalaryScore:
    def test_salary_meets_minimum_returns_one(self) -> None:
        score, reason = _salary_score(100000, 120000)
        assert score == 1.0
        assert "meets minimum" in reason

    def test_salary_exactly_at_minimum_returns_one(self) -> None:
        score, _ = _salary_score(100000, 100000)
        assert score == 1.0

    def test_salary_below_minimum_returns_zero(self) -> None:
        score, reason = _salary_score(150000, 100000)
        assert score == 0.0
        assert "below minimum" in reason

    def test_zero_minimum_always_returns_one(self) -> None:
        score, _ = _salary_score(0, 1)
        assert score == 1.0


# ── rank_jobs (integration of all dimensions) ─────────────────────────────────

class TestRankJobs:
    def test_empty_jobs_returns_empty_list(self) -> None:
        assert rank_jobs(_user(), []) == []

    def test_results_sorted_descending_by_score(self) -> None:
        user = _user()
        jobs = [_job() for _ in range(5)]
        ranked = rank_jobs(user, jobs)
        scores = [r.score for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_scores_bounded_between_zero_and_one(self) -> None:
        user = _user()
        jobs = [_job() for _ in range(5)]
        for r in rank_jobs(user, jobs):
            assert 0.0 <= r.score <= 1.0

    def test_perfect_match_ranks_first(self) -> None:
        user = _user()
        good = _job(title="Backend Engineer", required_skills=["python", "fastapi", "postgresql"])
        bad = _job(
            title="iOS Developer",
            required_skills=["swift", "objc"],
            salary=80000,
            remote=False,
            location="Austin",
        )
        ranked = rank_jobs(user, [bad, good])
        assert ranked[0].job.title == "Backend Engineer"
        assert ranked[0].score > ranked[1].score

    def test_salary_below_minimum_pushes_job_down(self) -> None:
        user = _user(salary_min=150000)
        ranked = rank_jobs(user, [_job(salary=100000), _job(salary=160000)])
        assert ranked[0].job.salary == 160000

    def test_under_experienced_user_gets_reason(self) -> None:
        user = _user(experience_years=1)
        ranked = rank_jobs(user, [_job(experience_min=5)])
        assert any("Under-experienced" in r for r in ranked[0].match_reasons)

    def test_remote_preference_beats_location_mismatch(self) -> None:
        user = _user(remote_ok=True, location="Tokyo")
        ranked = rank_jobs(
            user,
            [_job(remote=False, location="New York"), _job(remote=True, location="Remote")],
        )
        assert ranked[0].job.remote is True

    def test_match_reasons_count_equals_five(self) -> None:
        ranked = rank_jobs(_user(), [_job()])
        assert len(ranked[0].match_reasons) == 5

    def test_single_job_still_returns_ranked_job(self) -> None:
        ranked = rank_jobs(_user(), [_job()])
        assert len(ranked) == 1
        assert ranked[0].score >= 0.0

    def test_user_with_no_skills_gets_zero_skills_score(self) -> None:
        user = _user(skills=[])
        ranked = rank_jobs(user, [_job(required_skills=["python", "fastapi"])])
        assert any("0/" in r for r in ranked[0].match_reasons)

    def test_tied_jobs_all_appear_in_results(self) -> None:
        user = _user()
        jobs = [_job() for _ in range(3)]
        ranked = rank_jobs(user, jobs)
        assert len(ranked) == 3

    def test_perfect_match_score_is_one(self) -> None:
        # All 5 dimensions score 1.0: full skills overlap, role match,
        # experience ok, remote ok, salary met.
        user = _user(
            skills=["python", "fastapi"],
            preferred_roles=["backend engineer"],
            experience_years=4,
            location="San Francisco",
            remote_ok=True,
            salary_min=120000,
        )
        job = _job(
            title="Backend Engineer",
            required_skills=["python", "fastapi"],
            experience_min=3,
            remote=True,
            salary=150000,
        )
        ranked = rank_jobs(user, [job])
        assert ranked[0].score == 1.0

    def test_zero_match_score_is_zero(self) -> None:
        # All 5 dimensions score 0.0: no skills, wrong role,
        # under-experienced, location mismatch, salary too low.
        user = _user(
            skills=["java"],
            preferred_roles=["frontend engineer"],
            experience_years=1,
            location="New York",
            remote_ok=False,
            salary_min=200000,
        )
        job = _job(
            title="Backend Engineer",
            required_skills=["python"],
            experience_min=5,
            remote=False,
            location="San Francisco",
            salary=100000,
        )
        ranked = rank_jobs(user, [job])
        assert ranked[0].score == 0.0

    def test_partial_skills_match_gives_correct_weighted_score(self) -> None:
        # Skills: 2/3 matched (0.667) → 0.667 * 0.45 = 0.300
        # All other dimensions are 1.0 → 0.20 + 0.15 + 0.10 + 0.10 = 0.55
        # Total: 0.85
        user = _user(
            skills=["python", "fastapi", "postgresql"],
            preferred_roles=["backend engineer"],
            experience_years=4,
            remote_ok=True,
            salary_min=120000,
        )
        job = _job(
            title="Backend Engineer",
            required_skills=["python", "fastapi", "rust"],
            experience_min=3,
            remote=True,
            salary=150000,
        )
        ranked = rank_jobs(user, [job])
        assert ranked[0].score == pytest.approx(0.85, abs=1e-4)
