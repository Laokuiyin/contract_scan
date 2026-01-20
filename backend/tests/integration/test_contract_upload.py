import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO

def get_mock_db():
    """Mock database dependency"""
    session = MagicMock()
    return session

def test_upload_contract_success():
    """Test successful contract upload"""
    from app.main import app
    from app.schemas.contract import ContractResponse
    from app.models.enums import ContractType, ContractStatus
    from uuid import uuid4
    from datetime import datetime

    # Override dependencies
    app.dependency_overrides = {}

    # Create a real response object
    test_id = uuid4()
    test_time = datetime.now()

    response_data = {
        "id": test_id,
        "contract_number": "HT2024001",
        "contract_type": ContractType.PURCHASE,
        "file_path": "raw/test.pdf",
        "status": ContractStatus.PENDING_OCR,
        "upload_time": test_time,
        "created_by": None,
        "total_amount": None,
        "subject_matter": None,
        "sign_date": None,
        "effective_date": None,
        "expire_date": None,
        "confidence_score": None,
        "requires_review": True
    }

    # Create mock session and service
    mock_db = MagicMock()
    mock_service = Mock()
    mock_service.create_contract.return_value = ContractResponse(**response_data)

    # Mock MinIO service
    with patch('app.services.contract_service.MinIOService'):
        with patch('app.api.contracts.ContractService', return_value=mock_service):
            from app.core.db import get_db
            app.dependency_overrides[get_db] = lambda: mock_db

            client = TestClient(app)

            # Prepare test file
            file_content = b"test pdf content"
            files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
            data = {
                "contract_number": "HT2024001",
                "contract_type": "purchase"
            }

            # Make request
            response = client.post("/api/contracts/upload", files=files, data=data)

    # Clean up
    app.dependency_overrides = {}

    # Assertions
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["contract_number"] == "HT2024001"
    assert response_json["contract_type"] == "purchase"
    assert "id" in response_json
    assert "file_path" in response_json

def test_list_contracts_empty():
    """Test listing contracts when none exist"""
    from app.main import app
    from app.core.db import get_db

    mock_db = MagicMock()
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.get("/api/contracts/")

    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json() == []

def test_get_contract_not_found():
    """Test getting a non-existent contract"""
    from app.main import app
    from app.core.db import get_db

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.get("/api/contracts/nonexistent-id")

    app.dependency_overrides = {}

    assert response.status_code == 404
    assert "detail" in response.json()

def test_get_contract_success():
    """Test successfully getting a contract"""
    from app.main import app
    from app.core.db import get_db
    from app.models.enums import ContractType, ContractStatus
    from uuid import uuid4
    from datetime import datetime

    mock_db = MagicMock()

    mock_contract = Mock()
    mock_contract.id = str(uuid4())
    mock_contract.contract_number = "HT2024001"
    mock_contract.contract_type = ContractType.PURCHASE
    mock_contract.file_path = "raw/test.pdf"
    mock_contract.status = ContractStatus.PENDING_OCR
    mock_contract.upload_time = datetime.now()
    mock_contract.requires_review = True
    mock_contract.created_by = None
    mock_contract.total_amount = None
    mock_contract.subject_matter = None
    mock_contract.sign_date = None
    mock_contract.effective_date = None
    mock_contract.expire_date = None
    mock_contract.confidence_score = None

    mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.get(f"/api/contracts/{mock_contract.id}")

    app.dependency_overrides = {}

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["contract_number"] == "HT2024001"
    assert response_data["contract_type"] == "purchase"
