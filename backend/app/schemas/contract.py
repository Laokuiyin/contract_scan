from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from app.schemas.enums import ContractType, ContractStatus, PartyType

class ContractPartyBase(BaseModel):
    party_type: PartyType
    party_name: str
    party_type_detail: Optional[str] = None
    tax_number: Optional[str] = None
    legal_representative: Optional[str] = None
    address: Optional[str] = None
    contact_info: Optional[str] = None
    confidence_score: Optional[float] = None

class ContractPartyCreate(ContractPartyBase):
    pass

class ContractPartyResponse(ContractPartyBase):
    id: UUID
    contract_id: UUID
    model_config = ConfigDict(from_attributes=True)

class ContractBase(BaseModel):
    contract_number: str
    contract_type: ContractType

class ContractCreate(BaseModel):
    contract_number: str
    contract_type: str  # 改为接受字符串，避免枚举转换
    filename: Optional[str] = None  # 原始文件名

class ContractUpdate(BaseModel):
    total_amount: Optional[Decimal] = None
    subject_matter: Optional[str] = None
    sign_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None

class ContractResponse(ContractBase):
    id: UUID
    file_path: str
    status: ContractStatus
    upload_time: datetime
    created_by: Optional[str] = None
    total_amount: Optional[Decimal] = None
    subject_matter: Optional[str] = None
    sign_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None
    confidence_score: Optional[float] = None
    requires_review: bool
    model_config = ConfigDict(from_attributes=True)

class ContractListResponse(BaseModel):
    id: UUID
    contract_number: str
    contract_type: ContractType
    status: ContractStatus
    upload_time: datetime
    total_amount: Optional[Decimal] = None
    party_a_name: Optional[str] = None
    party_b_name: Optional[str] = None
    confidence_score: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)
