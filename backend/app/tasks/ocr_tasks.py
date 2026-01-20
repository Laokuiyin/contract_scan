"""Celery tasks for OCR processing"""

from celery import shared_task
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Contract
from app.models.enums import ContractStatus
from app.services.ocr_service import OCRService


@shared_task(name="app.tasks.ocr_tasks.process_ocr")
def process_ocr(contract_id: str) -> dict:
    """
    Process OCR for a contract

    Args:
        contract_id: UUID of the contract to process

    Returns:
        Dict with processing status and text file path
    """
    db: Session = next(get_db())
    ocr_service = OCRService()

    try:
        # Get contract from database
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return {"status": "error", "message": "Contract not found"}

        # Update status to processing
        contract.status = ContractStatus.OCR_PROCESSING
        db.commit()

        # Extract text using OCR
        text_path = ocr_service.extract_and_upload_text(contract.file_path)

        # Update contract with OCR result
        contract.ocr_text_path = text_path
        contract.status = ContractStatus.PENDING_AI_EXTRACTION
        db.commit()

        # Trigger AI extraction task
        from app.tasks.ai_extraction_tasks import process_ai_extraction
        process_ai_extraction.delay(contract_id)

        return {
            "status": "success",
            "contract_id": str(contract_id),
            "text_path": text_path
        }

    except Exception as e:
        # Update status to failed
        contract.status = ContractStatus.OCR_FAILED
        db.commit()

        return {
            "status": "error",
            "contract_id": str(contract_id),
            "message": str(e)
        }
    finally:
        db.close()
