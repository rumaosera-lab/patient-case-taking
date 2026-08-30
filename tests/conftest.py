import os
import mongomock
import pytest
from fastapi.testclient import TestClient

import backend.database.connection as db_conn
from backend.main import app


@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    """
    Provides a clean in-memory mongomock database for each test.
    """
    client = mongomock.MongoClient()
    db = client[db_conn.DB_NAME]

    # Patch database connection helpers across the backend modules
    db_conn._client = client
    monkeypatch.setattr(db_conn, "_client", client)
    monkeypatch.setattr(db_conn, "get_client", lambda: client)
    monkeypatch.setattr(db_conn, "get_db", lambda: db)
    monkeypatch.setattr(db_conn, "check_db_connection", lambda: True)
    
    # Ensure indexes on the mock DB
    db_conn.ensure_indexes(db)

    yield db


@pytest.fixture
def client():
    """
    Returns a FastAPI TestClient instance.
    """
    with TestClient(app) as test_client:
        yield test_client
