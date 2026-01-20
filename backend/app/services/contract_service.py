from sqlalchemy.orm import Session
from app.models.models import Contract
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
        return db.query(Contract).offset(skip).limit(limit).all()
