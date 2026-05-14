"""API integration tests for /api/v1/public/recommendations."""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.controller.recommendation import RecommendationController
from app.models.job import JobResponse
from app.models.recommendation import RankedJob, RecommendationResponse


_BASE = "/api/v1/public/recommendations"


def _ranked_job(score: float = 0.8) -> RankedJob:
    jid = uuid.uuid4()
    job = JobResponse(
        id=jid,
        title="Backend Engineer",
        company="ACME",
        required_skills=["python"],
        experience_min=2,
        location="SF",
        remote=True,
        salary=150000,
        description="",
        is_active=True,
    )
    return RankedJob(
        job=job,
        score=score,
        match_reasons=["Skills matched: python (1/1)", "Role matched", "Experience fit", "Remote match", "Salary OK"],
    )


def _recommendation(user_id: uuid.UUID, n_jobs: int = 2) -> RecommendationResponse:
    return RecommendationResponse(
        user_id=user_id,
        ranked_jobs=[_ranked_job(score=round(1.0 - i * 0.1, 1)) for i in range(n_jobs)],
    )


class TestGetRecommendations:
    def test_success_returns_200(self, client) -> None:
        uid = uuid.uuid4()
        result = _recommendation(uid)
        with patch.object(RecommendationController, "get_recommendations", return_value=result):
            resp = client.get(f"{_BASE}/{uid}")
        assert resp.status_code == 200

    def test_response_contains_user_id(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(RecommendationController, "get_recommendations",
                          return_value=_recommendation(uid)):
            body = client.get(f"{_BASE}/{uid}").json()["payload"]
        assert body["user_id"] == str(uid)

    def test_response_contains_ranked_jobs_list(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(RecommendationController, "get_recommendations",
                          return_value=_recommendation(uid, n_jobs=3)):
            body = client.get(f"{_BASE}/{uid}").json()["payload"]
        assert len(body["ranked_jobs"]) == 3

    def test_ranked_jobs_have_score_and_reasons(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(RecommendationController, "get_recommendations",
                          return_value=_recommendation(uid, n_jobs=1)):
            ranked = client.get(f"{_BASE}/{uid}").json()["payload"]["ranked_jobs"]
        assert "score" in ranked[0]
        assert "match_reasons" in ranked[0]
        assert isinstance(ranked[0]["match_reasons"], list)

    def test_jobs_sorted_descending_by_score(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(RecommendationController, "get_recommendations",
                          return_value=_recommendation(uid, n_jobs=4)):
            ranked = client.get(f"{_BASE}/{uid}").json()["payload"]["ranked_jobs"]
        scores = [r["score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_unknown_user_returns_404(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(
            RecommendationController, "get_recommendations",
            side_effect=HTTPException(404, f"User {uid} not found"),
        ):
            resp = client.get(f"{_BASE}/{uid}")
        assert resp.status_code == 404

    def test_invalid_uuid_returns_422(self, client) -> None:
        resp = client.get(f"{_BASE}/not-a-uuid")
        assert resp.status_code == 422

    def test_empty_job_pool_returns_empty_ranked_list(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(RecommendationController, "get_recommendations",
                          return_value=RecommendationResponse(user_id=uid, ranked_jobs=[])):
            body = client.get(f"{_BASE}/{uid}").json()["payload"]
        assert body["ranked_jobs"] == []

    def test_each_ranked_job_contains_job_details(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(RecommendationController, "get_recommendations",
                          return_value=_recommendation(uid, n_jobs=1)):
            ranked = client.get(f"{_BASE}/{uid}").json()["payload"]["ranked_jobs"]
        job = ranked[0]["job"]
        for field in ("id", "title", "company", "required_skills",
                      "salary", "remote", "location"):
            assert field in job
