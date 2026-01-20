from app.models.models import Contract, ContractParty
from app.models.enums import ContractType, ContractStatus, PartyType

def test_create_contract():
    contract = Contract(
        contract_number="HT2024001",
        contract_type=ContractType.PURCHASE,
        file_path="/contracts/test.pdf",
        created_by="test_user"
    )
    assert contract.contract_number == "HT2024001"
    assert contract.contract_type == ContractType.PURCHASE
    assert contract.status == ContractStatus.PENDING_OCR

def test_contract_with_party():
    contract = Contract(
        contract_number="HT2024001",
        contract_type=ContractType.PURCHASE,
        file_path="/contracts/test.pdf"
    )
    party = ContractParty(
        contract_id=contract.id,
        party_type=PartyType.PARTY_A,
        party_name="测试公司A"
    )
    assert party.party_name == "测试公司A"
