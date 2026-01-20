import os
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session, joinedload
from app.models.models import Contract
from app.schemas.contract import ContractCreate
from app.models.enums import PartyType

# 创建上传目录
UPLOAD_DIR = Path("/opt/contract_scan/contract_scan/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
RAW_DIR = UPLOAD_DIR / "raw"
RAW_DIR.mkdir(exist_ok=True)

class ContractService:
    def __init__(self):
        # 不再依赖 MinIO
        pass

    def save_file_locally(self, file_content: bytes, filename: str) -> str:
        """保存文件到本地存储"""
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = RAW_DIR / unique_filename

        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)

        return str(file_path)

    def create_contract(self, db: Session, contract_data: ContractCreate, file_content: bytes, created_by: str = None) -> Contract:
        # 获取文件扩展名
        filename = getattr(contract_data, 'filename', contract_data.contract_number)
        file_extension = filename.split('.')[-1] if '.' in filename else 'pdf'

        # 保存到本地
        file_path = self.save_file_locally(file_content, f"{filename}.{file_extension}")

        # 创建合同记录
        db_contract = Contract(
            contract_number=contract_data.contract_number,
            contract_type=contract_data.contract_type.lower(),  # 确保小写
            file_path=file_path,
            upload_time=datetime.utcnow(),
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
        return db.query(Contract)\
            .options(joinedload(Contract.parties))\
            .order_by(Contract.upload_time.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def serialize_contract_list(self, contracts: list) -> list:
        """Serialize contracts with party names for API response"""
        result = []
        for contract in contracts:
            party_a = next((p.party_name for p in contract.parties if p.party_type == PartyType.PARTY_A), None)
            party_b = next((p.party_name for p in contract.parties if p.party_type == PartyType.PARTY_B), None)

            result.append({
                "id": contract.id,
                "contract_number": contract.contract_number,
                "contract_type": contract.contract_type,
                "status": contract.status,
                "upload_time": contract.upload_time,
                "total_amount": contract.total_amount,
                "party_a_name": party_a,
                "party_b_name": party_b,
                "confidence_score": contract.confidence_score
            })
        return result
