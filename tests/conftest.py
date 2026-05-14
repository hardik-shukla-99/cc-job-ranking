import os

# Must be set before any app imports so config skips DB env validation
os.environ.setdefault("ENV", "test")

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.client import DBClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """TestClient with startup mocked and DB session overridden."""
    mock_db = MagicMock()
    app.dependency_overrides[DBClient.get_db_session] = lambda: mock_db
    with patch("app.main._init_resources"):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()
