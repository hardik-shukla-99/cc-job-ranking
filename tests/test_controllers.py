"""Unit tests for controllers — DB services mocked, no HTTP."""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.controller.job import JobController
from app.controller.recommendation import RecommendationController
from app.controller.user_profile import UserProfileController
from app.db.models.job import JobModel
from app.db.models.user_profile import UserProfileModel
from app.db.services.job import JobDB
from app.db.services.user_profile import UserProfileDB
from app.models.user_profile import UserProfileCreate
from app.models.job import JobCreate


def _mock_user(**overrides: object) -> MagicMock:
    m = MagicMock(spec=UserProfileModel)
    attrs = dict(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        skills=["python"],
        experience_years=3,
        preferred_roles=["backend engineer"],
        location="SF",
        remote_ok=True,
        salary_min=100000,
    )
    attrs.update(overrides)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def _mock_job(**overrides: object) -> MagicMock:
    m = MagicMock(spec=JobModel)
    attrs = dict(
        id=uuid.uuid4(),
        title="Backend Engineer",
        company="ACME",
        required_skills=["python"],
        experience_min=2,
        location="SF",
        remote=True,
        salary=120000,
        description="",
        is_active=True,
    )
    attrs.update(overrides)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


class TestUserProfileController:
    def setup_method(self) -> None:
        self.mock_db = MagicMock()

    def test_create_succeeds_when_no_duplicate(self) -> None:
        new_user = _mock_user()
        with patch.object(UserProfileDB, "get_by_filter", return_value=None), \
             patch.object(UserProfileDB, "create", return_value=new_user):
            result = UserProfileController(self.mock_db).create(
                UserProfileCreate(
                    name="Test User",
                    email="test@example.com",
                    skills=["python"],
                    experience_years=3,
                    preferred_roles=[],
                    location="SF",
                    remote_ok=True,
                    salary_min=100000,
                )
            )
        assert result == new_user

    def test_create_raises_409_on_duplicate_email(self) -> None:
        with patch.object(UserProfileDB, "get_by_filter", return_value=_mock_user()):
            with pytest.raises(HTTPException) as exc:
                UserProfileController(self.mock_db).create(
                    UserProfileCreate(
                        name="Dup",
                        email="dup@example.com",
                        skills=[],
                        experience_years=0,
                        preferred_roles=[],
                        location="",
                        remote_ok=False,
                        salary_min=0,
                    )
                )
        assert exc.value.status_code == 409

    def test_get_by_id_returns_user(self) -> None:
        user = _mock_user()
        with patch.object(UserProfileDB, "get_by_id", return_value=user):
            result = UserProfileController(self.mock_db).get_by_id(user.id)
        assert result == user

    def test_get_by_id_raises_404_when_missing(self) -> None:
        with patch.object(UserProfileDB, "get_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc:
                UserProfileController(self.mock_db).get_by_id(uuid.uuid4())
        assert exc.value.status_code == 404

    def test_404_message_contains_user_id(self) -> None:
        uid = uuid.uuid4()
        with patch.object(UserProfileDB, "get_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc:
                UserProfileController(self.mock_db).get_by_id(uid)
        assert str(uid) in exc.value.detail


class TestJobController:
    def setup_method(self) -> None:
        self.mock_db = MagicMock()

    def test_create_returns_job(self) -> None:
        job = _mock_job()
        with patch.object(JobDB, "create", return_value=job):
            result = JobController(self.mock_db).create(
                JobCreate(
                    title="Backend Engineer",
                    company="ACME",
                    required_skills=["python"],
                    experience_min=2,
                    location="SF",
                    remote=True,
                    salary=120000,
                    description="",
                )
            )
        assert result == job

    def test_list_active_returns_only_active_jobs(self) -> None:
        active = [_mock_job(is_active=True) for _ in range(3)]
        with patch.object(JobDB, "get_active_jobs", return_value=active):
            result = JobController(self.mock_db).list_active()
        assert result == active
        assert all(j.is_active for j in result)

    def test_list_active_returns_empty_list_when_none(self) -> None:
        with patch.object(JobDB, "get_active_jobs", return_value=[]):
            result = JobController(self.mock_db).list_active()
        assert result == []


class TestRecommendationController:
    def setup_method(self) -> None:
        self.mock_db = MagicMock()

    def test_returns_recommendation_response(self) -> None:
        user = _mock_user()
        jobs = [_mock_job()]
        with patch.object(UserProfileDB, "get_by_id", return_value=user), \
             patch.object(JobDB, "get_active_jobs", return_value=jobs):
            result = RecommendationController(self.mock_db).get_recommendations(user.id)
        assert result.user_id == user.id
        assert len(result.ranked_jobs) == 1

    def test_propagates_404_for_unknown_user(self) -> None:
        with patch.object(UserProfileDB, "get_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc:
                RecommendationController(self.mock_db).get_recommendations(uuid.uuid4())
        assert exc.value.status_code == 404

    def test_empty_jobs_returns_empty_ranked_list(self) -> None:
        user = _mock_user()
        with patch.object(UserProfileDB, "get_by_id", return_value=user), \
             patch.object(JobDB, "get_active_jobs", return_value=[]):
            result = RecommendationController(self.mock_db).get_recommendations(user.id)
        assert result.ranked_jobs == []

    def test_ranked_jobs_are_sorted_by_score_descending(self) -> None:
        user = _mock_user(skills=["python"], preferred_roles=["backend engineer"])
        good_job = _mock_job(title="Backend Engineer", required_skills=["python"], salary=200000)
        bad_job = _mock_job(title="iOS Developer", required_skills=["swift"], salary=50000, remote=False, location="Mars")
        with patch.object(UserProfileDB, "get_by_id", return_value=user), \
             patch.object(JobDB, "get_active_jobs", return_value=[bad_job, good_job]):
            result = RecommendationController(self.mock_db).get_recommendations(user.id)
        assert result.ranked_jobs[0].score >= result.ranked_jobs[1].score

    def test_all_ranked_scores_between_zero_and_one(self) -> None:
        user = _mock_user()
        jobs = [_mock_job() for _ in range(4)]
        with patch.object(UserProfileDB, "get_by_id", return_value=user), \
             patch.object(JobDB, "get_active_jobs", return_value=jobs):
            result = RecommendationController(self.mock_db).get_recommendations(user.id)
        for ranked in result.ranked_jobs:
            assert 0.0 <= ranked.score <= 1.0

    def test_each_ranked_job_has_five_match_reasons(self) -> None:
        user = _mock_user()
        with patch.object(UserProfileDB, "get_by_id", return_value=user), \
             patch.object(JobDB, "get_active_jobs", return_value=[_mock_job()]):
            result = RecommendationController(self.mock_db).get_recommendations(user.id)
        assert len(result.ranked_jobs[0].match_reasons) == 5
