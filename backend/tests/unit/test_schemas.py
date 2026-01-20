from app.schemas.contract import ContractCreate, ContractResponse, ContractPartyCreate, ContractPartyResponse
from app.schemas.enums import ContractType, ContractStatus, PartyType
from uuid import uuid4
from datetime import datetime

def test_contract_create_schema():
    """Test ContractCreate schema validation"""
    contract_data = {
        "contract_number": "HT2024001",
        "contract_type": ContractType.PURCHASE,
        "file": b"fake file content"
    }
    contract = ContractCreate(**contract_data)
    assert contract.contract_number == "HT2024001"
    assert contract.contract_type == ContractType.PURCHASE
    assert contract.file == b"fake file content"

def test_contract_party_create_schema():
    """Test ContractPartyCreate schema validation"""
    party_data = {
        "party_type": PartyType.PARTY_A,
        "party_name": "Test Company Ltd.",
        "tax_number": "123456789",
        "legal_representative": "John Doe",
        "address": "123 Main St",
        "contact_info": "contact@test.com",
        "confidence_score": 0.95
    }
    party = ContractPartyCreate(**party_data)
    assert party.party_type == PartyType.PARTY_A
    assert party.party_name == "Test Company Ltd."
    assert party.tax_number == "123456789"
    assert party.confidence_score == 0.95

def test_contract_response_schema():
    """Test ContractResponse schema with all fields"""
    contract_data = {
        "id": uuid4(),
        "contract_number": "HT2024001",
        "contract_type": ContractType.SALES,
        "file_path": "raw/test.pdf",
        "status": ContractStatus.PENDING_OCR,
        "upload_time": datetime.now(),
        "created_by": "test_user",
        "total_amount": "100000.00",
        "subject_matter": "Software Development",
        "sign_date": datetime.now(),
        "effective_date": datetime.now(),
        "expire_date": datetime.now(),
        "confidence_score": 0.92,
        "requires_review": True
    }
    contract = ContractResponse(**contract_data)
    assert contract.contract_number == "HT2024001"
    assert contract.contract_type == ContractType.SALES
    assert contract.status == ContractStatus.PENDING_OCR
    assert contract.requires_review == True

def test_contract_party_response_schema():
    """Test ContractPartyResponse schema"""
    party_data = {
        "id": uuid4(),
        "contract_id": uuid4(),
        "party_type": PartyType.PARTY_B,
        "party_name": "Vendor Corp",
        "tax_number": "987654321",
        "confidence_score": 0.88
    }
    party = ContractPartyResponse(**party_data)
    assert party.party_type == PartyType.PARTY_B
    assert party.party_name == "Vendor Corp"
    assert party.confidence_score == 0.88
