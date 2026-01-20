"""OCR processing functions"""

from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Contract, ContractFile
from app.services.ocr_service import OCRService
import tempfile
import os


def process_ocr(contract_id: str) -> dict:
    """
    Process OCR for a contract (supports multiple files)

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

        # 获取合同的所有文件，按顺序排列
        contract_files = db.query(ContractFile)\
            .filter(ContractFile.contract_id == contract_id)\
            .order_by(ContractFile.file_order)\
            .all()

        if not contract_files:
            # 兼容旧数据：如果没有 ContractFile，使用 file_path
            if not contract.file_path:
                return {"status": "error", "message": "No files found for contract"}

            # 单文件处理（旧数据）
            text = ocr_service.extract_text_from_file(contract.file_path)
            all_text_parts = [text]
        else:
            # 多文件处理：按顺序提取每个文件的文本
            all_text_parts = []
            for cf in contract_files:
                try:
                    text = ocr_service.extract_text_from_file(cf.file_path)
                    all_text_parts.append(text)
                except Exception as e:
                    print(f"Error processing file {cf.filename}: {e}")
                    all_text_parts.append(f"[文件 {cf.filename} 识别失败]")

        # 合并所有文本（按页顺序）
        combined_text = "\n\n=== 下一页 ===\n\n".join(all_text_parts)

        # 保存合并后的文本到文件
        text_path = os.path.join(
            os.path.dirname(contract_files[0].file_path if contract_files else contract.file_path),
            f"{contract.contract_number}_ocr.txt"
        )
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(combined_text)

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
                "files_processed": len(contract_files) if contract_files else 1,
                "ai_extraction": ai_result
            }
        except Exception as ai_error:
            # AI 提取失败不影响 OCR 结果
            return {
                "status": "success_with_ai_warning",
                "contract_id": str(contract_id),
                "text_path": text_path,
                "files_processed": len(contract_files) if contract_files else 1,
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
