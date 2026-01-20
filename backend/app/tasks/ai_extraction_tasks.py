"""Celery tasks for AI extraction"""

import json
from celery import shared_task
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Contract, ContractParty, AIExtractionResult
from app.models.enums import ContractStatus, PartyType
from app.services.ai_extraction_service import AIExtractionService
from datetime import datetime


@shared_task(name="app.tasks.ai_extraction_tasks.process_ai_extraction")
def process_ai_extraction(contract_id: str) -> dict:
    """
    Process AI extraction for a contract

    Args:
        contract_id: UUID of the contract to process

    Returns:
        Dict with processing status and extracted fields
    """
    import asyncio

    db: Session = next(get_db())
    ai_service = AIExtractionService()

    try:
        # Get contract from database
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return {"status": "error", "message": "Contract not found"}

        if not contract.ocr_text_path:
            return {"status": "error", "message": "OCR text not found"}

        # Update status to processing
        contract.status = ContractStatus.AI_PROCESSING
        db.commit()

        # Extract fields using AI
        result = asyncio.run(ai_service.extract_from_minio_file(contract.ocr_text_path))
        extracted = result["extracted_data"]
        confidence = result["confidence_score"]

        # Update contract with extracted fields
        contract.total_amount = extracted.get("total_amount")
        contract.subject_matter = extracted.get("subject_matter")

        # Parse dates
        for date_field in ["sign_date", "effective_date", "expire_date"]:
            date_str = extracted.get(date_field)
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    setattr(contract, date_field, date_obj)
                except (ValueError, TypeError):
                    pass

        contract.confidence_score = confidence
        contract.requires_review = confidence < 0.8

        # Save extraction results to AIExtractionResult table
        for field_name, value in extracted.items():
            if field_name != "parties" and value is not None:
                extraction_result = AIExtractionResult(
                    contract_id=contract.id,
                    field_name=field_name,
                    raw_value=str(value),
                    reasoning=json.dumps({"source": "ai_extraction"}),
                    confidence_score=confidence,
                    model_version=result["model_version"]
                )
                db.add(extraction_result)

        # Process parties
        if extracted.get("parties"):
            # Clear existing parties
            db.query(ContractParty).filter(ContractParty.contract_id == contract.id).delete()

            # Add new parties
            for party_data in extracted["parties"]:
                party_type_str = party_data.get("party_type", "甲方")
                party_type = PartyType.PARTY_A if "甲" in party_type_str else PartyType.PARTY_B

                party = ContractParty(
                    contract_id=contract.id,
                    party_type=party_type,
                    party_name=party_data.get("party_name", ""),
                    tax_number=party_data.get("tax_number"),
                    legal_representative=party_data.get("legal_representative"),
                    address=party_data.get("address"),
                    confidence_score=confidence
                )
                db.add(party)

        # Update status to completed
        contract.status = ContractStatus.COMPLETED
        db.commit()

        return {
            "status": "success",
            "contract_id": str(contract_id),
            "extracted_fields": list(extracted.keys()),
            "confidence_score": confidence
        }

    except Exception as e:
        # Update status to failed - Reset to allow retry
        contract.status = ContractStatus.PENDING_AI
        db.commit()

        return {
            "status": "error",
            "contract_id": str(contract_id),
            "message": str(e)
        }
    finally:
        db.close()
