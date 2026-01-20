from enum import Enum

class ContractType(str, Enum):
    PURCHASE = "purchase"  # 采购合同
    SALES = "sales"        # 销售合同
    LEASE = "lease"        # 租赁合同

class ContractStatus(str, Enum):
    PENDING_OCR = "pending_ocr"
    OCR_PROCESSING = "ocr_processing"
    PENDING_AI = "pending_ai"
    AI_PROCESSING = "ai_processing"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"

class PartyType(str, Enum):
    PARTY_A = "party_a"  # 甲方
    PARTY_B = "party_b"  # 乙方

class PartyTypeDetail(str, Enum):
    COMPANY = "company"
    INDIVIDUAL = "individual"
    GOVERNMENT = "government"
