from enum import Enum

class ContractType(str, Enum):
    PURCHASE = "purchase"
    SALES = "sales"
    LEASE = "lease"

class ContractStatus(str, Enum):
    PENDING_OCR = "pending_ocr"
    OCR_PROCESSING = "ocr_processing"
    PENDING_AI = "pending_ai"
    AI_PROCESSING = "ai_processing"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"

class PartyType(str, Enum):
    PARTY_A = "party_a"
    PARTY_B = "party_b"
