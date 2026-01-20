"""OCR processing functions"""

from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Contract
from app.services.ocr_service import OCRService


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
        contract.status = "ocr_processing"
        db.commit()

        # Extract text using OCR
        text_path = ocr_service.extract_and_save_text(contract.file_path)

        # Update contract with OCR result
        contract.ocr_text_path = text_path
        contract.status = "pending_ai"  # 待AI提取
        db.commit()

        # 自动触发 AI 提取
        try:
            from app.tasks.ai_extraction_tasks import process_ai_extraction
            ai_result = process_ai_extraction(contract_id)
            return {
                "status": "success",
                "contract_id": str(contract_id),
                "text_path": text_path,
                "ai_extraction": ai_result
            }
        except Exception as ai_error:
            # AI 提取失败不影响 OCR 结果
            return {
                "status": "success_with_ai_warning",
                "contract_id": str(contract_id),
                "text_path": text_path,
                "message": f"OCR completed, but AI extraction failed: {str(ai_error)}"
            }

    except Exception as e:
        # Update status to failed
        contract.status = "pending_ocr"  # 失败后重置状态
        db.commit()

        return {
            "status": "error",
            "contract_id": str(contract_id),
            "message": str(e)
        }
    finally:
        db.close()
