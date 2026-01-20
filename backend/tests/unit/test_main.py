from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

@pytest.fixture
def client():
    """Create a test client with mocked database"""
    with patch('app.main.Base.metadata.create_all'):
        from app.main import app
        with TestClient(app) as test_client:
            yield test_client

def test_read_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Contract Scanner API"}

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_contracts_list(client):
    """Test contracts list endpoint returns empty list by default"""
    from unittest.mock import MagicMock
    from app.core.db import get_db

    # Mock database session
    mock_db = MagicMock()
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

    # Override dependency
    from app.main import app
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/contracts/")
    assert response.status_code == 200
    assert response.json() == []

    # Clean up
    app.dependency_overrides = {}
