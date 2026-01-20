# Contract List Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix contract status display issue and add party names (甲乙方) + amount fields to contract list view

**Architecture:**
- Fix incorrect enum values in AI extraction tasks causing status to be stuck at "pending_ai"
- Modify backend API to return parties and amount in list response
- Update frontend to display extracted information when available

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, Element Plus

**Root Cause Analysis:**
1. `ai_extraction_tasks.py:39,111` use non-existent enum values `AI_EXTRACTION_PROCESSING` and `AI_EXTRACTION_FAILED`
2. `ContractListResponse` schema only includes basic fields, not parties or amount
3. List API doesn't eager-load parties relationship

---

## Task 1: Fix AI Extraction Task Enum Values

**Files:**
- Modify: `backend/app/tasks/ai_extraction_tasks.py:39,111`

**Step 1: Read the enum definitions**

Run: `cat backend/app/schemas/enums.py`
Expected: See that only `ai_processing` exists, not `AI_EXTRACTION_PROCESSING`

**Step 2: Fix incorrect enum value at line 39**

Change:
```python
contract.status = ContractStatus.AI_EXTRACTION_PROCESSING
```

To:
```python
contract.status = ContractStatus.AI_PROCESSING
```

**Step 3: Fix incorrect enum value at line 111**

Change:
```python
contract.status = ContractStatus.AI_EXTRACTION_FAILED
```

To:
```python
contract.status = ContractStatus.PENDING_AI  # Reset to allow retry
```

**Step 4: Commit**

```bash
git add backend/app/tasks/ai_extraction_tasks.py
git commit -m "fix: use correct enum values in AI extraction task"
```

---

## Task 2: Update ContractListResponse Schema

**Files:**
- Modify: `backend/app/schemas/contract.py:57-64`

**Step 1: Add new fields to ContractListResponse**

Replace existing `ContractListResponse` class:

```python
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
```

**Step 2: Commit**

```bash
git add backend/app/schemas/contract.py
git commit -m "feat: add party names and amount to ContractListResponse"
```

---

## Task 3: Update Contract Service to Load Parties

**Files:**
- Modify: `backend/app/services/contract_service.py:58-60`

**Step 1: Update list_contracts method to eager-load parties**

Replace:
```python
def list_contracts(self, db: Session, skip: int = 0, limit: int = 100):
    """List contracts with pagination"""
    return db.query(Contract).offset(skip).limit(limit).all()
```

With:
```python
from sqlalchemy.orm import joinedload

def list_contracts(self, db: Session, skip: int = 0, limit: int = 100):
    """List contracts with pagination"""
    return db.query(Contract)\
        .options(joinedload(Contract.parties))\
        .order_by(Contract.upload_time.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
```

**Step 2: Add method to serialize contract with parties**

Add after `list_contracts` method:

```python
def serialize_contract_list(self, contracts: list) -> list:
    """Serialize contracts with party names for API response"""
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
```

**Step 3: Update imports at top**

Add to imports:
```python
from app.models.enums import PartyType
```

**Step 4: Commit**

```bash
git add backend/app/services/contract_service.py
git commit -m "feat: eager-load parties and add serialization method"
```

---

## Task 4: Update Contract API Endpoints

**Files:**
- Modify: `backend/app/api/contracts.py:63-84`

**Step 1: Update list_contracts endpoint**

Replace:
```python
@router.get("/", response_model=list[ContractListResponse])
def list_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    contracts = db.query(Contract).offset(skip).limit(limit).all()
    return contracts
```

With:
```python
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
```

**Step 2: Update get_pending_review_contracts endpoint**

Replace:
```python
@router.get("/pending-review", response_model=List[ContractListResponse])
def get_pending_review_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取待审核合同列表"""
    contracts = db.query(Contract)\
        .filter(Contract.requires_review == True)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return contracts
```

With:
```python
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
```

**Step 3: Commit**

```bash
git add backend/app/api/contracts.py
git commit -m "feat: update list endpoints to include party names and amount"
```

---

## Task 5: Update Frontend Contract List View

**Files:**
- Modify: `frontend/src/views/ContractList.vue:13-39`

**Step 1: Add new columns to el-table**

Insert after line 28 (after status column):

```vue
<el-table-column prop="party_a_name" label="甲方名称" width="200">
  <template #default="{ row }">
    {{ row.party_a_name || '-' }}
  </template>
</el-table-column>
<el-table-column prop="party_b_name" label="乙方名称" width="200">
  <template #default="{ row }">
    {{ row.party_b_name || '-' }}
  </template>
</el-table-column>
<el-table-column prop="total_amount" label="合同金额" width="150">
  <template #default="{ row }">
    {{ row.total_amount ? `¥${formatAmount(row.total_amount)}` : '-' }}
  </template>
</el-table-column>
```

**Step 2: Add formatAmount utility function**

Add after `formatDate` function (around line 66):

```javascript
const formatAmount = (amount: number | string) => {
  if (!amount) return '0.00'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}
```

**Step 3: Commit**

```bash
git add frontend/src/views/ContractList.vue
git commit -m "feat: display party names and amount in contract list"
```

---

## Task 6: Add Status for AI Extraction Failed

**Files:**
- Modify: `backend/app/schemas/enums.py:10-16`
- Modify: `frontend/src/views/ContractList.vue:88-101`

**Step 1: Add failed status to backend enum**

Add to `ContractStatus` enum:

```python
class ContractStatus(str, Enum):
    PENDING_OCR = "pending_ocr"
    OCR_PROCESSING = "ocr_processing"
    PENDING_AI = "pending_ai"
    AI_PROCESSING = "ai_processing"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    FAILED = "failed"
```

**Step 2: Update frontend status labels**

Add to `getStatusLabel` function:

```javascript
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending_ocr: '待OCR识别',
    ocr_processing: 'OCR处理中',
    pending_ai: '待AI提取',
    ai_processing: 'AI提取中',
    pending_review: '待审核',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}
```

**Step 3: Update frontend status tag types**

Add to `getStatusTagType` function:

```javascript
const getStatusTagType = (status: string) => {
  const types: Record<string, any> = {
    pending_ocr: 'info',
    ocr_processing: 'warning',
    pending_ai: 'info',
    ai_processing: 'warning',
    pending_review: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || ''
}
```

**Step 4: Commit**

```bash
git add backend/app/schemas/enums.py frontend/src/views/ContractList.vue
git commit -m "feat: add failed status for better error tracking"
```

---

## Task 7: Test the Implementation

**Step 1: Restart backend services**

Run: `docker-compose -f docker-compose.dev.yml restart backend`

**Step 2: Check backend logs**

Run: `docker-compose -f docker-compose.dev.yml logs -f backend --tail=50`
Expected: No errors, services start successfully

**Step 3: Trigger OCR for a test contract**

Open browser: `http://localhost:5173/contracts`
Action: Click "手动触发OCR" on a contract with status "待AI提取"
Expected: Status changes from "待AI提取" → "AI提取中" → "已完成" (or "失败")

**Step 4: Verify contract list displays new fields**

Open browser: `http://localhost:5173/contracts`
Expected:
- See columns for "甲方名称", "乙方名称", "合同金额"
- When extraction completes, party names and amounts are displayed
- When pending/failed, shows "-"

**Step 5: Verify API response**

Run: `curl http://localhost:8000/api/contracts/ | jq`
Expected: Response includes `party_a_name`, `party_b_name`, `total_amount` fields

**Step 6: Commit**

```bash
git add .
git commit -m "test: verify contract list enhancement works correctly"
```

---

## Summary

This plan addresses:
1. **Root cause fix**: Correct enum values preventing AI extraction from completing
2. **Feature addition**: Display party names and contract amounts in list view
3. **User experience**: Show "-" when data not available, format currency properly
4. **Error handling**: Add failed status for better visibility
