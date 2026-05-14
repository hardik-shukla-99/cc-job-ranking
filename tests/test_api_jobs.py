"""API integration tests for /api/v1/public/jobs."""
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.controller.job import JobController
from app.db.models.job import JobModel


_BASE = "/api/v1/public/jobs"

_VALID_PAYLOAD = {
    "title": "Backend Engineer",
    "company": "ACME Corp",
    "required_skills": ["python", "fastapi"],
    "experience_min": 3,
    "location": "San Francisco",
    "remote": True,
    "salary": 150000,
    "description": "Build APIs.",
}


def _mock_job(**overrides: object) -> MagicMock:
    m = MagicMock(spec=JobModel)
    attrs = {**_VALID_PAYLOAD, "id": uuid.uuid4(), "is_active": True}
    attrs.update(overrides)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


class TestCreateJob:
    def test_success_returns_201(self, client) -> None:
        with patch.object(JobController, "create", return_value=_mock_job()):
            resp = client.post(_BASE, json=_VALID_PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["status"] == 201

    def test_response_contains_job_fields(self, client) -> None:
        jid = uuid.uuid4()
        with patch.object(JobController, "create", return_value=_mock_job(id=jid)):
            body = client.post(_BASE, json=_VALID_PAYLOAD).json()["payload"]
        assert body["id"] == str(jid)
        assert body["title"] == _VALID_PAYLOAD["title"]
        assert body["company"] == _VALID_PAYLOAD["company"]

    def test_missing_title_returns_422(self, client) -> None:
        resp = client.post(_BASE, json={k: v for k, v in _VALID_PAYLOAD.items() if k != "title"})
        assert resp.status_code == 422

    def test_missing_company_returns_422(self, client) -> None:
        resp = client.post(_BASE, json={k: v for k, v in _VALID_PAYLOAD.items() if k != "company"})
        assert resp.status_code == 422

    def test_empty_skills_list_accepted(self, client) -> None:
        with patch.object(JobController, "create", return_value=_mock_job(required_skills=[])):
            resp = client.post(_BASE, json={**_VALID_PAYLOAD, "required_skills": []})
        assert resp.status_code == 201

    def test_zero_salary_accepted(self, client) -> None:
        with patch.object(JobController, "create", return_value=_mock_job(salary=0)):
            resp = client.post(_BASE, json={**_VALID_PAYLOAD, "salary": 0})
        assert resp.status_code == 201


class TestListJobs:
    def test_returns_200_with_list(self, client) -> None:
        jobs = [_mock_job() for _ in range(3)]
        with patch.object(JobController, "list_active", return_value=jobs):
            resp = client.get(_BASE)
        assert resp.status_code == 200
        assert len(resp.json()["payload"]) == 3

    def test_empty_list_when_no_jobs(self, client) -> None:
        with patch.object(JobController, "list_active", return_value=[]):
            resp = client.get(_BASE)
        assert resp.status_code == 200
        assert resp.json()["payload"] == []

    def test_each_job_has_required_fields(self, client) -> None:
        with patch.object(JobController, "list_active", return_value=[_mock_job()]):
            payload = client.get(_BASE).json()["payload"]
        job = payload[0]
        for field in ("id", "title", "company", "required_skills",
                      "experience_min", "location", "remote", "salary", "is_active"):
            assert field in job

    def test_only_active_jobs_returned(self, client) -> None:
        active_jobs = [_mock_job(is_active=True), _mock_job(is_active=True)]
        with patch.object(JobController, "list_active", return_value=active_jobs):
            payload = client.get(_BASE).json()["payload"]
        assert all(j["is_active"] for j in payload)
