from sqlalchemy.orm import Session, joinedload
from app.models.models import Contract
from app.models.enums import PartyType
from app.schemas.contract import ContractCreate
from app.services.minio_service import MinIOService
import uuid

class ContractService:
    def __init__(self):
        self.minio_service = MinIOService()

    def create_contract(self, db: Session, contract_data: ContractCreate, file_content: bytes, created_by: str = None) -> Contract:
        # Generate unique filename
        file_extension = "pdf"  # Simplified
        filename = f"{uuid.uuid4()}.{file_extension}"

        # Upload to MinIO
        file_path = self.minio_service.upload_file(file_content, filename, "raw")

        # Create contract record
        db_contract = Contract(
            contract_number=contract_data.contract_number,
            contract_type=contract_data.contract_type,
            file_path=file_path,
            created_by=created_by or "system"
        )
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)

        return db_contract

    def get_contract(self, db: Session, contract_id: str) -> Contract:
        """Get a contract by ID"""
        return db.query(Contract).filter(Contract.id == contract_id).first()

    def list_contracts(self, db: Session, skip: int = 0, limit: int = 100):
        """List contracts with pagination"""
        return db.query(Contract).options(joinedload(Contract.parties)).order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()

    def serialize_contract_list(self, contracts):
        """Serialize a list of contracts with their parties"""
        return [
            {
                "id": str(contract.id),
                "contract_number": contract.contract_number,
                "contract_type": contract.contract_type,
                "status": contract.status,
                "created_at": contract.created_at.isoformat() if contract.created_at else None,
                "parties": [
                    {
                        "id": str(party.id),
                        "name": party.name,
                        "role": party.role,
                        "party_type": party.party_type.value if party.party_type else None,
                        "organization_id": str(party.organization_id) if party.organization_id else None
                    }
                    for party in contract.parties
                ]
            }
            for contract in contracts
        ]
