from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.db import get_db
from app.schemas.contract import ContractResponse, ContractListResponse
from app.schemas.review import ReviewRecordCreate, ReviewRecordResponse, ReviewSummary
from app.models.models import Contract, ReviewRecord, ContractFile
from app.services.contract_service import ContractService
from uuid import UUID
import os

router = APIRouter()

@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    files: List[UploadFile] = File(...),  # 改为支持多文件
    contract_number: str = Form(...),
    contract_type: str = Form(...),
    db: Session = Depends(get_db)
):
    from app.schemas.contract import ContractCreate

    # 读取所有文件内容
    files_content = []
    for file in files:
        file_content = await file.read()
        files_content.append((file.filename, file_content))

    # 确保 contract_type 是小写字符串
    contract_type_lower = contract_type.lower() if isinstance(contract_type, str) else str(contract_type).lower()

    # Create contract data
    contract_data = ContractCreate(
        contract_number=contract_number,
        contract_type=contract_type_lower
    )

    # Save contract（支持多文件）
    service = ContractService()
    contract = service.create_contract(db, contract_data, files_content)

    # 自动触发 OCR 识别（加入队列）
    try:
        from app.services.ocr_queue import ocr_queue_manager
        queue_status = ocr_queue_manager.add_task(str(contract.id))
        print(f"Contract {contract.contract_number} added to OCR queue: {queue_status}")
    except Exception as e:
        print(f"Failed to add contract to OCR queue: {e}")

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

@router.post("/{contract_id}/ocr", response_model=ContractResponse)
def trigger_ocr(contract_id: str, db: Session = Depends(get_db)):
    """触发OCR识别（加入队列）"""
    from app.services.ocr_queue import ocr_queue_manager

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # 检查状态是否允许触发OCR
    if contract.status not in ["pending_ocr", "ocr_failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot trigger OCR for contract with status: {contract.status}"
        )

    # 添加到队列
    queue_status = ocr_queue_manager.add_task(contract_id)

    # 更新状态
    contract.status = "ocr_processing"
    db.commit()

    return contract

@router.get("/{contract_id}/ocr-text")
def get_ocr_text(contract_id: str, db: Session = Depends(get_db)):
    """获取合同的OCR识别文本"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.ocr_text_path:
        return {
            "contract_id": contract_id,
            "ocr_text": None,
            "message": "OCR识别尚未完成"
        }

    try:
        import os
        if os.path.exists(contract.ocr_text_path):
            with open(contract.ocr_text_path, 'r', encoding='utf-8') as f:
                ocr_text = f.read()
            return {
                "contract_id": contract_id,
                "ocr_text": ocr_text,
                "ocr_text_path": contract.ocr_text_path,
                "message": "OCR识别已完成"
            }
        else:
            return {
                "contract_id": contract_id,
                "ocr_text": None,
                "message": "OCR文本文件不存在"
            }
    except Exception as e:
        return {
            "contract_id": contract_id,
            "ocr_text": None,
            "message": f"读取OCR文本失败: {str(e)}"
        }

@router.delete("/{contract_id}")
def delete_contract(contract_id: str, db: Session = Depends(get_db)):
    """删除单个合同"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # 删除合同（级联删除关联的parties、extraction_results、review_records）
    db.delete(contract)
    db.commit()

    return {"message": "Contract deleted successfully", "contract_id": contract_id}

@router.post("/batch-delete")
def batch_contracts(contract_ids: List[str], db: Session = Depends(get_db)):
    """批量删除合同"""
    if not contract_ids:
        raise HTTPException(status_code=400, detail="No contract IDs provided")

    # 查询要删除的合同
    contracts = db.query(Contract).filter(Contract.id.in_(contract_ids)).all()

    if not contracts:
        raise HTTPException(status_code=404, detail="No contracts found")

    # 删除所有合同
    for contract in contracts:
        db.delete(contract)

    db.commit()

    return {
        "message": f"Successfully deleted {len(contracts)} contracts",
        "deleted_count": len(contracts),
        "contract_ids": [str(c.id) for c in contracts]
    }

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


# Contract files management endpoints
@router.get("/{contract_id}/files")
def get_contract_files(contract_id: str, db: Session = Depends(get_db)):
    """获取合同的文件列表"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # 获取合同的所有文件，按顺序排列
    files = db.query(ContractFile)\
        .filter(ContractFile.contract_id == contract_id)\
        .order_by(ContractFile.file_order)\
        .all()

    return [{
        "id": str(f.id),
        "filename": f.filename,
        "file_path": f.file_path,
        "file_order": f.file_order,
        "upload_time": f.upload_time
    } for f in files]


@router.get("/files/{file_id}/download")
def download_contract_file(file_id: str, db: Session = Depends(get_db)):
    """下载/打开合同文件"""
    from urllib.parse import quote

    contract_file = db.query(ContractFile).filter(ContractFile.id == file_id).first()
    if not contract_file:
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(contract_file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # 根据文件扩展名确定 MIME 类型
    filename_lower = contract_file.filename.lower()
    if filename_lower.endswith('.pdf'):
        media_type = 'application/pdf'
    elif filename_lower.endswith(('.jpg', '.jpeg')):
        media_type = 'image/jpeg'
    elif filename_lower.endswith('.png'):
        media_type = 'image/png'
    elif filename_lower.endswith('.gif'):
        media_type = 'image/gif'
    else:
        media_type = 'application/octet-stream'

    # 对文件名进行 URL 编码，支持中文
    encoded_filename = quote(contract_file.filename)

    # 使用 inline 让浏览器在页面中显示，而不是下载
    return FileResponse(
        path=contract_file.file_path,
        media_type=media_type,
        headers={
            'Content-Disposition': f'inline; filename*=UTF-8\'\'{encoded_filename}'
        }
    )


@router.delete("/{contract_id}/files/{file_id}")
def delete_contract_file(contract_id: str, file_id: str, db: Session = Depends(get_db)):
    """删除合同文件并清空相关字段"""
    # 获取合同和文件
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract_file = db.query(ContractFile).filter(
        ContractFile.id == file_id,
        ContractFile.contract_id == contract_id
    ).first()
    if not contract_file:
        raise HTTPException(status_code=404, detail="File not found")

    # 删除物理文件
    try:
        if os.path.exists(contract_file.file_path):
            os.remove(contract_file.file_path)
    except Exception as e:
        print(f"Failed to delete file {contract_file.file_path}: {e}")

    # 删除数据库记录
    db.delete(contract_file)

    # 检查是否还有其他文件
    remaining_files = db.query(ContractFile)\
        .filter(ContractFile.contract_id == contract_id)\
        .count()

    # 如果没有文件了，或者这是最后一个文件，清空 AI 提取字段
    if remaining_files == 0:
        # 清空所有 AI 提取字段
        contract.total_amount = None
        contract.subject_matter = None
        contract.sign_date = None
        contract.effective_date = None
        contract.expire_date = None
        contract.confidence_score = None
        contract.ocr_text_path = None
        contract.status = "pending_ocr"  # 重置状态
        contract.requires_review = True

        # 删除所有相关数据
        db.query(ReviewRecord).filter(ReviewRecord.contract_id == contract.id).delete()
        from app.models.models import ContractParty, AIExtractionResult
        db.query(ContractParty).filter(ContractParty.contract_id == contract.id).delete()
        db.query(AIExtractionResult).filter(AIExtractionResult.contract_id == contract.id).delete()

    db.commit()

    return {
        "message": "File deleted successfully",
        "file_id": file_id,
        "remaining_files": remaining_files,
        "fields_cleared": remaining_files == 0
    }

