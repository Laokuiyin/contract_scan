from sqlalchemy import Column, String, DateTime, Text, Numeric, Boolean, ForeignKey, Enum as SQLEnum, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.models.enums import ContractType, ContractStatus, PartyType

from app.core.db import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_number = Column(String(100), unique=True, nullable=False, index=True)
    contract_type = Column(SQLEnum(ContractType), nullable=False)
    file_path = Column(String(500), nullable=False)
    ocr_text_path = Column(String(500))
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.PENDING_OCR, nullable=False, index=True)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))

    def __init__(self, **kwargs):
        if 'status' not in kwargs:
            kwargs['status'] = ContractStatus.PENDING_OCR
        super().__init__(**kwargs)

    # 提取字段
    total_amount = Column(Numeric(15, 2))
    subject_matter = Column(Text)
    sign_date = Column(DateTime)
    effective_date = Column(DateTime)
    expire_date = Column(DateTime)

    confidence_score = Column(Float)
    requires_review = Column(Boolean, default=True)

    # Relationships
    parties = relationship("ContractParty", back_populates="contract", cascade="all, delete-orphan")
    extraction_results = relationship("AIExtractionResult", back_populates="contract", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="contract", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_contract_type_date', 'contract_type', 'sign_date'),
        Index('ix_confidence_score', 'confidence_score'),
    )


class ContractParty(Base):
    __tablename__ = "contract_parties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    party_type = Column(SQLEnum(PartyType), nullable=False)
    party_name = Column(String(500), nullable=False)
    party_type_detail = Column(String(50))
    tax_number = Column(String(50))
    legal_representative = Column(String(100))
    address = Column(Text)
    contact_info = Column(Text)  # JSON
    confidence_score = Column(Float)

    contract = relationship("Contract", back_populates="parties")


class AIExtractionResult(Base):
    __tablename__ = "ai_extraction_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    raw_value = Column(Text)
    reasoning = Column(Text)  # JSON
    confidence_score = Column(Float)
    model_version = Column(String(50))
    prompt_template = Column(String(100))
    extract_time = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="extraction_results")


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    ai_value = Column(Text)
    human_value = Column(Text)
    reviewer = Column(String(100), nullable=False)
    review_time = Column(DateTime(timezone=True), server_default=func.now())
    is_correct = Column(Boolean)
    notes = Column(Text)

    contract = relationship("Contract", back_populates="review_records")
