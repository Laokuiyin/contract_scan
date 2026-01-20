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
    """Test contracts list endpoint (placeholder)"""
    response = client.get("/api/contracts/")
    assert response.status_code == 200
    assert response.json() == []

def test_contracts_upload_placeholder(client):
    """Test contracts upload endpoint (placeholder)"""
    response = client.post("/api/contracts/upload")
    assert response.status_code == 200
    assert response.json() == {"message": "Not implemented yet"}
