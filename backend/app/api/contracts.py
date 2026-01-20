from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.db import get_db
from app.schemas.contract import ContractResponse, ContractListResponse
from app.schemas.review import ReviewRecordCreate, ReviewRecordResponse, ReviewSummary
from app.models.models import Contract, ReviewRecord
from app.services.contract_service import ContractService
from uuid import UUID

router = APIRouter()

@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    contract_number: str = Form(...),
    contract_type: str = Form(...),
    db: Session = Depends(get_db)
):
    from app.schemas.contract import ContractCreate

    # Read file content
    file_content = await file.read()

    # 确保 contract_type 是小写字符串
    contract_type_lower = contract_type.lower() if isinstance(contract_type, str) else str(contract_type).lower()

    # Create contract data
    contract_data = ContractCreate(
        contract_number=contract_number,
        contract_type=contract_type_lower,  # 使用小写字符串
        filename=file.filename
    )

    # Save contract
    service = ContractService()
    contract = service.create_contract(db, contract_data, file_content)

    return contract

@router.get("/", response_model=list[ContractListResponse])
def list_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    from app.models.enums import PartyType

    contracts = db.query(Contract)\
        .options(joinedload(Contract.parties))\
        .order_by(Contract.upload_time.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    # Serialize with party names
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

@router.get("/pending-review", response_model=List[ContractListResponse])
def get_pending_review_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取待审核合同列表"""
    from sqlalchemy.orm import joinedload
    from app.models.enums import PartyType

    contracts = db.query(Contract)\
        .options(joinedload(Contract.parties))\
        .filter(Contract.requires_review == True)\
        .order_by(Contract.upload_time.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    # Serialize with party names
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

@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

# Review endpoints
@router.post("/review", response_model=ReviewRecordResponse)
def create_review(review_data: ReviewRecordCreate, contract_id: UUID, db: Session = Depends(get_db)):
    """创建审核记录"""
    # Verify contract exists
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Create review record
    review = ReviewRecord(
        contract_id=contract_id,
        field_name=review_data.field_name,
        ai_value=review_data.ai_value,
        human_value=review_data.human_value,
        reviewer=review_data.reviewer,
        is_correct=review_data.is_correct,
        notes=review_data.notes
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@router.get("/{contract_id}/reviews", response_model=List[ReviewRecordResponse])
def get_contract_reviews(contract_id: UUID, db: Session = Depends(get_db)):
    """获取合同的所有审核记录"""
    # Verify contract exists
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    reviews = db.query(ReviewRecord).filter(ReviewRecord.contract_id == contract_id).all()
    return reviews

