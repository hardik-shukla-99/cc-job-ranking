"""API integration tests for /api/v1/public/users."""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.controller.user_profile import UserProfileController
from app.db.models.user_profile import UserProfileModel


_BASE = "/api/v1/public/users"

_VALID_PAYLOAD = {
    "name": "Alice Dev",
    "email": "alice@example.com",
    "skills": ["python", "fastapi"],
    "experience_years": 3,
    "preferred_roles": ["backend engineer"],
    "location": "San Francisco",
    "remote_ok": True,
    "salary_min": 120000,
}


def _mock_user(**overrides: object) -> MagicMock:
    m = MagicMock(spec=UserProfileModel)
    attrs = {**_VALID_PAYLOAD, "id": uuid.uuid4()}
    attrs.update(overrides)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


class TestCreateUser:
    def test_success_returns_201_with_payload(self, client) -> None:
        mock_user = _mock_user()
        with patch.object(UserProfileController, "create", return_value=mock_user):
            resp = client.post(_BASE, json=_VALID_PAYLOAD)
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == 201
        assert body["payload"]["email"] == _VALID_PAYLOAD["email"]
        assert body["payload"]["name"] == _VALID_PAYLOAD["name"]

    def test_response_contains_id(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(UserProfileController, "create", return_value=_mock_user(id=uid)):
            resp = client.post(_BASE, json=_VALID_PAYLOAD)
        assert resp.json()["payload"]["id"] == str(uid)

    def test_duplicate_email_returns_409(self, client) -> None:
        with patch.object(
            UserProfileController, "create",
            side_effect=HTTPException(409, "User with email 'alice@example.com' already exists"),
        ):
            resp = client.post(_BASE, json=_VALID_PAYLOAD)
        assert resp.status_code == 409

    def test_missing_email_returns_422(self, client) -> None:
        resp = client.post(_BASE, json={"name": "No Email"})
        assert resp.status_code == 422

    def test_missing_name_returns_422(self, client) -> None:
        resp = client.post(_BASE, json={"email": "x@example.com"})
        assert resp.status_code == 422

    def test_invalid_email_format_returns_422(self, client) -> None:
        resp = client.post(_BASE, json={**_VALID_PAYLOAD, "email": "not-an-email"})
        assert resp.status_code == 422

    def test_negative_salary_min_accepted(self, client) -> None:
        mock_user = _mock_user(salary_min=-1)
        with patch.object(UserProfileController, "create", return_value=mock_user):
            resp = client.post(_BASE, json={**_VALID_PAYLOAD, "salary_min": -1})
        assert resp.status_code == 201

    def test_empty_skills_list_accepted(self, client) -> None:
        mock_user = _mock_user(skills=[])
        with patch.object(UserProfileController, "create", return_value=mock_user):
            resp = client.post(_BASE, json={**_VALID_PAYLOAD, "skills": []})
        assert resp.status_code == 201

    def test_only_required_fields_accepted(self, client) -> None:
        with patch.object(UserProfileController, "create", return_value=_mock_user()):
            resp = client.post(_BASE, json={"name": "Bob", "email": "bob@example.com"})
        assert resp.status_code == 201

    def test_zero_experience_years_accepted(self, client) -> None:
        with patch.object(UserProfileController, "create", return_value=_mock_user(experience_years=0)):
            resp = client.post(_BASE, json={**_VALID_PAYLOAD, "experience_years": 0})
        assert resp.status_code == 201

    def test_negative_experience_years_accepted(self, client) -> None:
        with patch.object(UserProfileController, "create", return_value=_mock_user(experience_years=-1)):
            resp = client.post(_BASE, json={**_VALID_PAYLOAD, "experience_years": -1})
        assert resp.status_code == 201


class TestGetUser:
    def test_success_returns_200(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(UserProfileController, "get_by_id", return_value=_mock_user(id=uid)):
            resp = client.get(f"{_BASE}/{uid}")
        assert resp.status_code == 200
        assert resp.json()["payload"]["id"] == str(uid)

    def test_not_found_returns_404(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(
            UserProfileController, "get_by_id",
            side_effect=HTTPException(404, f"User {uid} not found"),
        ):
            resp = client.get(f"{_BASE}/{uid}")
        assert resp.status_code == 404

    def test_invalid_uuid_returns_422(self, client) -> None:
        resp = client.get(f"{_BASE}/not-a-uuid")
        assert resp.status_code == 422

    def test_response_includes_all_profile_fields(self, client) -> None:
        uid = uuid.uuid4()
        with patch.object(UserProfileController, "get_by_id", return_value=_mock_user(id=uid)):
            body = client.get(f"{_BASE}/{uid}").json()["payload"]
        for field in ("id", "name", "email", "skills", "experience_years",
                      "preferred_roles", "location", "remote_ok", "salary_min"):
            assert field in body
