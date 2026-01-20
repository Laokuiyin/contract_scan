from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from app.core.db import get_db
from app.schemas.contract import ContractResponse, ContractListResponse
from app.models.models import Contract
from app.services.contract_service import ContractService

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

    # Create contract data
    contract_data = ContractCreate(
        contract_number=contract_number,
        contract_type=contract_type,
        file=file_content
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
    contracts = db.query(Contract).offset(skip).limit(limit).all()
    return contracts

@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract
