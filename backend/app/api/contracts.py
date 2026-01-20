from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db

router = APIRouter()

@router.get("/", response_model=List)
def list_contracts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return []

@router.post("/upload")
def upload_contract():
    return {"message": "Not implemented yet"}
