# 历史合同扫描识别系统 - 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 开发一个支持合同文件上传、OCR识别、AI信息提取和人工审核的历史合同扫描识别系统

**Architecture:** 分层微服务架构 - FastAPI后端 + Vue3前端 + Celery异步任务 + PostgreSQL存储 + MinIO对象存储 + AI服务集成

**Tech Stack:**
- 后端: FastAPI 0.104+, Python 3.11, SQLAlchemy 2.0, Celery 5.3+, Redis 7.0, PostgreSQL 16
- 前端: Vue 3.3+, Vite 5.0, Element Plus, Pinia, TypeScript
- 存储: MinIO对象存储
- AI服务: 通义千问/GPT-4o-mini, 百度/腾讯云OCR

---

## Phase 1: 项目初始化和基础设施

### Task 1.1: 创建项目目录结构

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `frontend/src/main.ts`
- Create: `docker-compose.dev.yml`
- Create: `docker-compose.prod.yml`
- Create: `.env.example`

**Step 1: 创建后端目录结构**

```bash
mkdir -p backend/app/{api,models,schemas,services,tasks,core}
mkdir -p backend/tests/{unit,integration}
mkdir -p backend/alembic/versions
touch backend/app/__init__.py
```

**Step 2: 创建前端目录结构**

```bash
mkdir -p frontend/src/{components,views,stores,api,utils,types}
mkdir -p frontend/public
touch frontend/src/main.ts
```

**Step 3: 创建Docker配置文件**

创建 `docker-compose.dev.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: contract_scanner
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

**Step 4: 创建环境变量模板**

创建 `.env.example`:
```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contract_scanner

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_RAW=contract-raw
MINIO_BUCKET_TEXT=contract-text

# AI Services
AI_PROVIDER=qwen  # qwen or openai
QWEN_API_KEY=your_qwen_api_key
OPENAI_API_KEY=your_openai_api_key

# OCR
OCR_PROVIDER=baidu  # baidu or tencent
BAIDU_OCR_API_KEY=your_api_key
BAIDU_OCR_SECRET_KEY=your_secret_key

# Security
SECRET_KEY=your-secret-key-change-in-production
```

**Step 5: 提交初始结构**

```bash
git add .
git commit -m "feat: initialize project directory structure"
```

---

### Task 1.2: 配置后端依赖和基础配置

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/db.py`

**Step 1: 创建依赖文件**

创建 `backend/requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
celery==5.3.4
redis==5.0.1
minio==7.2.0
python-multipart==0.0.6
aiofiles==23.2.1
httpx==0.25.2
python-docx==1.1.0
pdfplumber==0.10.3
paddleocr==2.7.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

**Step 2: 创建配置模块**

创建 `backend/app/core/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_raw: str = "contract-raw"
    minio_bucket_text: str = "contract-text"
    minio_secure: bool = False

    ai_provider: str = "qwen"
    qwen_api_key: str = ""
    openai_api_key: str = ""

    ocr_provider: str = "baidu"
    baidu_ocr_api_key: str = ""
    baidu_ocr_secret_key: str = ""

    secret_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 3: 创建数据库连接模块**

创建 `backend/app/core/db.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4: 编写配置测试**

创建 `backend/tests/unit/test_config.py`:
```python
from app.core.config import settings

def test_settings_loaded():
    assert settings.database_url is not None
    assert settings.redis_url is not None
    assert settings.minio_endpoint is not None
```

**Step 5: 运行测试验证配置**

```bash
cd backend
pytest tests/unit/test_config.py -v
```

**Step 6: 提交配置**

```bash
git add backend/requirements.txt backend/app/core/ backend/tests/unit/test_config.py
git commit -m "feat: add backend configuration and database setup"
```

---

### Task 1.3: 创建数据库模型

**Files:**
- Create: `backend/app/models/models.py`
- Create: `backend/app/models/enums.py`

**Step 1: 创建枚举类型**

创建 `backend/app/models/enums.py`:
```python
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
```

**Step 2: 创建数据库模型**

创建 `backend/app/models/models.py`:
```python
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
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.PENDING_OCR, index=True)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))

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
```

**Step 3: 编写模型测试**

创建 `backend/tests/unit/test_models.py`:
```python
from app.models.models import Contract, ContractParty
from app.models.enums import ContractType, ContractStatus

def test_create_contract():
    contract = Contract(
        contract_number="HT2024001",
        contract_type=ContractType.PURCHASE,
        file_path="/contracts/test.pdf",
        created_by="test_user"
    )
    assert contract.contract_number == "HT2024001"
    assert contract.contract_type == ContractType.PURCHASE
    assert contract.status == ContractStatus.PENDING_OCR

def test_contract_with_party():
    contract = Contract(
        contract_number="HT2024001",
        contract_type=ContractType.PURCHASE,
        file_path="/contracts/test.pdf"
    )
    party = ContractParty(
        contract_id=contract.id,
        party_type="party_a",
        party_name="测试公司A"
    )
    assert party.party_name == "测试公司A"
```

**Step 4: 运行模型测试**

```bash
cd backend
pytest tests/unit/test_models.py -v
```

**Step 5: 提交模型**

```bash
git add backend/app/models/ backend/tests/unit/test_models.py
git commit -m "feat: add database models"
```

---

### Task 1.4: 配置数据库迁移

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

**Step 1: 初始化Alembic**

```bash
cd backend
alembic init alembic
```

**Step 2: 配置alembic/env.py**

编辑 `backend/alembic/env.py`:
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.db import Base
from app.models import *  # noqa

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 3: 配置alembic.ini**

编辑 `backend/alembic.ini`中的sqlalchemy.url:
```ini
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/contract_scanner
```

**Step 4: 创建初始迁移**

```bash
cd backend
alembic revision --autogenerate -m "Initial migration"
```

**Step 5: 测试迁移**

```bash
docker-compose -f docker-compose.dev.yml up -d postgres
cd backend
alembic upgrade head
```

**Step 6: 提交迁移配置**

```bash
git add backend/alembic/
git commit -m "feat: configure database migrations"
```

---

### Task 1.5: 创建MinIO服务模块

**Files:**
- Create: `backend/app/services/minio_service.py`

**Step 1: 编写MinIO服务测试**

创建 `backend/tests/unit/test_minio_service.py`:
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_minio_client():
    with patch('app.services.minio_service.Minio') as mock:
        yield mock

def test_minio_service_upload(mock_minio_client):
    from app.services.minio_service import MinIOService

    service = MinIOService()
    mock_client = mock_minio_client.return_value

    # Test upload
    file_path = service.upload_file(b"test content", "test.pdf", "raw")
    assert file_path is not None
    mock_client.put_object.assert_called_once()
```

**Step 2: 运行测试（预期失败）**

```bash
cd backend
pytest tests/unit/test_minio_service.py -v
```

预期: FAIL - MinIOService not defined

**Step 3: 实现MinIO服务**

创建 `backend/app/services/minio_service.py`:
```python
from minio import Minio
from app.core.config import settings
import io

class MinIOService:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self._ensure_buckets_exist()

    def _ensure_buckets_exist(self):
        for bucket in [settings.minio_bucket_raw, settings.minio_bucket_text]:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    def upload_file(self, content: bytes, filename: str, bucket_type: str = "raw") -> str:
        bucket = settings.minio_bucket_raw if bucket_type == "raw" else settings.minio_bucket_text
        object_name = f"{filename}"
        self.client.put_object(
            bucket,
            object_name,
            io.BytesIO(content),
            length=len(content)
        )
        return f"{bucket}/{object_name}"

    def get_file(self, file_path: str) -> bytes:
        bucket, object_name = file_path.split("/", 1)
        response = self.client.get_object(bucket, object_name)
        return response.read()

    def delete_file(self, file_path: str):
        bucket, object_name = file_path.split("/", 1)
        self.client.remove_object(bucket, object_name)
```

**Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/unit/test_minio_service.py -v
```

预期: PASS

**Step 5: 提交MinIO服务**

```bash
git add backend/app/services/minio_service.py backend/tests/unit/test_minio_service.py
git commit -m "feat: add MinIO service for file storage"
```

---

## Phase 2: 后端API开发

### Task 2.1: 创建Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/contract.py`
- Create: `backend/app/schemas/enums.py`

**Step 1: 创建枚举Schema**

创建 `backend/app/schemas/enums.py`:
```python
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
```

**Step 2: 创建合同Schema**

创建 `backend/app/schemas/contract.py`:
```python
from pydantic import BaseModel, Field
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

    class Config:
        from_attributes = True

class ContractBase(BaseModel):
    contract_number: str
    contract_type: ContractType

class ContractCreate(ContractBase):
    file: bytes  # 上传的文件内容

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

    class Config:
        from_attributes = True

class ContractListResponse(BaseModel):
    id: UUID
    contract_number: str
    contract_type: ContractType
    status: ContractStatus
    upload_time: datetime

    class Config:
        from_attributes = True
```

**Step 3: 编写Schema测试**

创建 `backend/tests/unit/test_schemas.py`:
```python
from app.schemas.contract import ContractCreate, ContractResponse
from app.schemas.enums import ContractType

def test_contract_create_schema():
    contract_data = {
        "contract_number": "HT2024001",
        "contract_type": ContractType.PURCHASE,
        "file": b"fake file content"
    }
    contract = ContractCreate(**contract_data)
    assert contract.contract_number == "HT2024001"
    assert contract.contract_type == ContractType.PURCHASE
```

**Step 4: 运行Schema测试**

```bash
cd backend
pytest tests/unit/test_schemas.py -v
```

**Step 5: 提交Schema**

```bash
git add backend/app/schemas/ backend/tests/unit/test_schemas.py
git commit -m "feat: add Pydantic schemas for contract data"
```

---

### Task 2.2: 创建FastAPI主应用

**Files:**
- Create: `backend/app/main.py`
- Modify: `backend/app/__init__.py`

**Step 1: 编写FastAPI应用测试**

创建 `backend/tests/unit/test_main.py`:
```python
from fastapi.testclient import TestClient

def test_read_root():
    from app.main import app
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Contract Scanner API"}

def test_health_check():
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

**Step 2: 运行测试（预期失败）**

```bash
cd backend
pytest tests/unit/test_main.py -v
```

预期: FAIL - app not defined

**Step 3: 实现FastAPI主应用**

创建 `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import contracts, health
from app.core.db import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contract Scanner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])

@app.get("/")
def read_root():
    return {"message": "Contract Scanner API"}
```

**Step 4: 创建健康检查路由**

创建 `backend/app/api/health.py`:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def health_check():
    return {"status": "healthy"}
```

**Step 5: 创建合同路由占位符**

创建 `backend/app/api/contracts.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from typing import List

router = APIRouter()

@router.get("/", response_model=List)
def list_contracts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return []

@router.post("/upload")
def upload_contract():
    return {"message": "Not implemented yet"}
```

**Step 6: 运行测试验证通过**

```bash
cd backend
pytest tests/unit/test_main.py -v
```

预期: PASS

**Step 7: 提交主应用**

```bash
git add backend/app/main.py backend/app/api/ backend/tests/unit/test_main.py
git commit -m "feat: create FastAPI main application"
```

---

### Task 2.3: 实现合同上传API

**Files:**
- Modify: `backend/app/api/contracts.py`
- Create: `backend/app/services/contract_service.py`

**Step 1: 编写合同上传测试**

创建 `backend/tests/integration/test_contract_upload.py`:
```python
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

def test_upload_contract_success():
    from app.main import app
    client = TestClient(app)

    file_content = b"fake contract content"
    files = {"file": ("contract.pdf", file_content, "application/pdf")}
    data = {
        "contract_number": "HT2024001",
        "contract_type": "purchase"
    }

    with patch('app.services.contract_service.MinIOService') as mock_minio:
        mock_minio_instance = Mock()
        mock_minio.return_value = mock_minio_instance
        mock_minio_instance.upload_file.return_value = "raw/contract.pdf"

        with patch('app.services.contract_service.redis_client') as mock_redis:
            response = client.post("/api/contracts/upload", files=files, data=data)

    assert response.status_code == 200
    data = response.json()
    assert data["contract_number"] == "HT2024001"
    assert data["status"] == "pending_ocr"
```

**Step 2: 运行测试（预期失败）**

```bash
cd backend
pytest tests/integration/test_contract_upload.py -v
```

预期: FAIL - upload_contract endpoint not implemented

**Step 3: 实现合同服务**

创建 `backend/app/services/contract_service.py`:
```python
from sqlalchemy.orm import Session
from app.models.models import Contract
from app.schemas.contract import ContractCreate
from app.services.minio_service import MinIOService
import uuid
from datetime import datetime

class ContractService:
    def __init__(self):
        self.minio_service = MinIOService()

    def create_contract(self, db: Session, contract_data: ContractCreate, file_content: bytes, created_by: str = None) -> Contract:
        # Generate unique filename
        file_extension = contract_data.file.name.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"

        # Upload to MinIO
        file_path = self.minio_service.upload_file(file_content, filename, "raw")

        # Create contract record
        db_contract = Contract(
            contract_number=contract_data.contract_number,
            contract_type=contract_data.contract_type,
            file_path=file_path,
            created_by=created_by or "system"
        )
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)

        return db_contract
```

**Step 4: 实现上传API端点**

编辑 `backend/app/api/contracts.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from app.core.db import get_db
from app.schemas.contract import ContractResponse, ContractListResponse
from app.models.models import Contract
from app.services.contract_service import ContractService
from app.tasks.ocr_tasks import process_ocr

router = APIRouter()

@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    contract_number: str = Form(...),
    contract_type: str = Form(...),
    db: Session = Depends(get_db)
):
    from app.schemas.contract import ContractCreate

    # Read file content
    file_content = await file.read()

    # Create contract data
    contract_data = ContractCreate(
        contract_number=contract_number,
        contract_type=contract_type,
        file=file_content
    )

    # Save contract
    service = ContractService()
    contract = service.create_contract(db, contract_data, file_content)

    # Trigger OCR task (async)
    process_ocr.delay(str(contract.id))

    return contract

@router.get("/", response_model=list[ContractListResponse])
def list_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    contracts = db.query(Contract).offset(skip).limit(limit).all()
    return contracts

@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract
```

**Step 5: 运行测试验证通过**

```bash
cd backend
pytest tests/integration/test_contract_upload.py -v
```

预期: PASS

**Step 6: 提交上传功能**

```bash
git add backend/app/api/contracts.py backend/app/services/contract_service.py backend/tests/integration/test_contract_upload.py
git commit -m "feat: implement contract upload API endpoint"
```

---

## Phase 3: OCR和AI提取

### Task 3.1: 配置Celery任务队列

**Files:**
- Create: `backend/app/worker.py`
- Create: `backend/app/tasks/__init__.py`

**Step 1: 编写Celery配置测试**

创建 `backend/tests/unit/test_celery_config.py`:
```python
from app.tasks.celery_app import celery_app

def test_celery_app_configured():
    assert celery_app.conf.broker_url is not None
    assert celery_app.conf.result_backend is not None
    assert 'ocr_tasks' in celery_app.conf.task_routes
```

**Step 2: 运行测试（预期失败）**

```bash
cd backend
pytest tests/unit/test_celery_config.py -v
```

预期: FAIL - celery_app not defined

**Step 3: 创建Celery应用**

创建 `backend/app/tasks/celery_app.py`:
```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "contract_scanner",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

celery_app.conf.task_routes = {
    "app.tasks.ocr_tasks.*": {"queue": "ocr"},
    "app.tasks.ai_extraction_tasks.*": {"queue": "ai"},
}
```

**Step 4: 创建Celery Worker入口**

创建 `backend/app/worker.py`:
```python
from app.tasks.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()
```

**Step 5: 运行测试验证通过**

```bash
cd backend
pytest tests/unit/test_celery_config.py -v
```

预期: PASS

**Step 6: 提交Celery配置**

```bash
git add backend/app/tasks/celery_app.py backend/app/worker.py backend/tests/unit/test_celery_config.py
git commit -m "feat: configure Celery task queue"
```

---

### Task 3.2: 实现OCR处理任务

**Files:**
- Create: `backend/app/tasks/ocr_tasks.py`
- Create: `backend/app/services/ocr_service.py`

**Step 1: 编写OCR服务测试**

创建 `backend/tests/unit/test_ocr_service.py`:
```python
from unittest.mock import Mock, patch
import pytest

@pytest.fixture
def ocr_service():
    from app.services.ocr_service import OCRService
    return OCRService()

def test_extract_text_from_pdf(ocr_service):
    # Mock pdfplumber
    with patch('app.services.ocr_service.pdfplumber') as mock_pdf:
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample contract text"
        mock_pdf.open.return_value.__enter__.return_value.pages = [mock_page]

        result = ocr_service.extract_from_pdf(b"fake pdf content")

    assert "Sample contract text" in result

def test_extract_text_from_image(ocr_service):
    with patch.object(ocr_service, '_extract_with_baidu_ocr') as mock_ocr:
        mock_ocr.return_value = "Image text result"

        result = ocr_service.extract_from_image(b"fake image content")

    assert result == "Image text result"
```

**Step 2: 运行测试（预期失败）**

```bash
cd backend
pytest tests/unit/test_ocr_service.py -v
```

预期: FAIL - OCRService not defined

**Step 3: 实现OCR服务**

创建 `backend/app/services/ocr_service.py`:
```python
import pdfplumber
import io
from app.core.config import settings
from typing import Optional

class OCRService:
    def __init__(self):
        self.ocr_provider = settings.ocr_provider

    def extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF using pdfplumber"""
        text = ""
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def extract_from_image(self, file_content: bytes) -> str:
        """Extract text from image using cloud OCR API"""
        if self.ocr_provider == "baidu":
            return self._extract_with_baidu_ocr(file_content)
        elif self.ocr_provider == "tencent":
            return self._extract_with_tencent_ocr(file_content)
        else:
            raise ValueError(f"Unsupported OCR provider: {self.ocr_provider}")

    def _extract_with_baidu_ocr(self, file_content: bytes) -> str:
        """Extract text using Baidu OCR API"""
        # TODO: Implement Baidu OCR API call
        # For now, return placeholder
        return "Baidu OCR extraction - not yet implemented"

    def _extract_with_tencent_ocr(self, file_content: bytes) -> str:
        """Extract text using Tencent OCR API"""
        # TODO: Implement Tencent OCR API call
        return "Tencent OCR extraction - not yet implemented"

    def extract_from_docx(self, file_content: bytes) -> str:
        """Extract text from Word document"""
        from docx import Document
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
```

**Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/unit/test_ocr_service.py -v
```

预期: PASS

**Step 5: 实现Celery OCR任务**

创建 `backend/app/tasks/ocr_tasks.py`:
```python
from celery import shared_task
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.models import Contract
from app.models.enums import ContractStatus
from app.services.ocr_service import OCRService
from app.services.minio_service import MinIOService
import io

@shared_task(name="app.tasks.ocr_tasks.process_ocr")
def process_ocr(contract_id: str):
    """Process OCR for a contract"""
    db: Session = SessionLocal()
    ocr_service = OCRService()
    minio_service = MinIOService()

    try:
        # Get contract
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Update status
        contract.status = ContractStatus.OCR_PROCESSING
        db.commit()

        # Download file from MinIO
        file_content = minio_service.get_file(contract.file_path)

        # Determine file type and extract text
        if contract.file_path.endswith('.pdf'):
            text = ocr_service.extract_from_pdf(file_content)
        elif contract.file_path.endswith(('.png', '.jpg', '.jpeg')):
            text = ocr_service.extract_from_image(file_content)
        elif contract.file_path.endswith('.docx'):
            text = ocr_service.extract_from_docx(file_content)
        else:
            raise ValueError(f"Unsupported file type: {contract.file_path}")

        # Save extracted text to MinIO
        text_filename = f"{contract_id}.txt"
        ocr_text_path = minio_service.upload_file(
            text.encode('utf-8'),
            text_filename,
            "text"
        )

        # Update contract
        contract.ocr_text_path = ocr_text_path
        contract.status = ContractStatus.PENDING_AI
        db.commit()

        # Trigger AI extraction task
        from app.tasks.ai_extraction_tasks import process_ai_extraction
        process_ai_extraction.delay(contract_id)

        return {"status": "success", "contract_id": contract_id}

    except Exception as e:
        contract.status = ContractStatus.PENDING_OCR
        db.commit()
        raise e
    finally:
        db.close()
```

**Step 6: 提交OCR实现**

```bash
git add backend/app/services/ocr_service.py backend/app/tasks/ocr_tasks.py backend/tests/unit/test_ocr_service.py
git commit -m "feat: implement OCR processing service and task"
```

---

### Task 3.3: 实现AI信息提取服务

**Files:**
- Create: `backend/app/services/ai_extraction_service.py`
- Create: `backend/app/tasks/ai_extraction_tasks.py`

**Step 1: 编写AI提取服务测试**

创建 `backend/tests/unit/test_ai_extraction.py`:
```python
from unittest.mock import Mock, patch
import pytest

@pytest.fixture
def ai_service():
    from app.services.ai_extraction_service import AIExtractionService
    return ai_service

def test_classify_contract(ai_service):
    with patch.object(ai_service, '_call_qwen_api') as mock_api:
        mock_api.return_value = "采购合同"

        result = ai_service.classify_contract("Sample contract text about purchasing goods")

    assert result == "purchase"

def test_extract_contract_info(ai_service):
    mock_response = {
        "contract_number": {"value": "HT2024001", "confidence": 95, "reasoning": "Found in header"},
        "total_amount": {"value": "100000.00", "confidence": 98, "reasoning": "Clear amount specified"}
    }

    with patch.object(ai_service, '_call_qwen_api') as mock_api:
        mock_api.return_value = mock_response

        result = ai_service.extract_info("Contract text", "purchase")

    assert "contract_number" in result
    assert result["contract_number"]["value"] == "HT2024001"
```

**Step 2: 运行测试（预期失败）**

```bash
cd backend
pytest tests/unit/test_ai_extraction.py -v
```

预期: FAIL - AIExtractionService not defined

**Step 3: 实现AI提取服务**

创建 `backend/app/services/ai_extraction_service.py`:
```python
import httpx
import json
from app.core.config import settings
from typing import Dict, Any

class AIExtractionService:
    def __init__(self):
        self.provider = settings.ai_provider
        self.api_key = settings.qwen_api_key if self.provider == "qwen" else settings.openai_api_key

    def classify_contract(self, text: str) -> str:
        """Classify contract type using AI"""
        prompt = f"""你是一个合同分类专家。请根据以下合同文本,判断合同类型。

合同类型:
- 采购合同: 买方购买商品或服务的合同
- 销售合同: 卖方出售商品或合同的合同
- 租赁合同: 关于房屋、设备等租赁的合同

合同文本:
{text[:2000]}  # Limit text length

请只返回合同类型(采购合同/销售合同/租赁合同),不要其他内容。"""

        response = self._call_qwen_api(prompt)

        # Map Chinese to enum
        type_map = {
            "采购合同": "purchase",
            "销售合同": "sales",
            "租赁合同": "lease"
        }
        return type_map.get(response.strip(), "purchase")

    def extract_info(self, text: str, contract_type: str) -> Dict[str, Any]:
        """Extract structured information from contract"""

        if contract_type == "purchase":
            prompt = self._get_purchase_extraction_prompt(text)
        elif contract_type == "sales":
            prompt = self._get_sales_extraction_prompt(text)
        else:
            prompt = self._get_lease_extraction_prompt(text)

        response = self._call_qwen_api(prompt)

        # Parse JSON response
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # If AI didn't return valid JSON, return empty dict
            return {}

    def _get_purchase_extraction_prompt(self, text: str) -> str:
        return f"""你是一个合同信息提取专家。请从以下采购合同中提取关键信息,并以JSON格式返回。

合同文本:
{text[:4000]}

请提取以下字段:
1. contract_number: 合同编号,查找"合同编号"、"协议编号"等关键词
2. party_a: 甲方(采购方)信息，包含name(名称), tax_number(税号), legal_rep(法人), address(地址)
3. party_b: 乙方(供应商)信息，同上
4. total_amount: 合同金额
5. subject_matter: 合同标的物
6. sign_date: 签订日期(YYYY-MM-DD格式)
7. effective_date: 生效日期(YYYY-MM-DD格式)
8. expire_date: 到期日期(YYYY-MM-DD格式)

返回格式:
{{
  "contract_number": {{"value": "...", "confidence": 95, "reasoning": "..."}},
  "party_a_name": {{"value": "...", "confidence": 90, "reasoning": "..."}},
  "total_amount": {{"value": "...", "confidence": 98, "reasoning": "..."}},
  ...
}}

注意:
- confidence为0-100的数字
- 如果找不到字段,value为null,confidence为0
- 金额必须找到明确数字"""

    def _get_sales_extraction_prompt(self, text: str) -> str:
        # Similar to purchase but adjusted for sales contracts
        return self._get_purchase_extraction_prompt(text)

    def _get_lease_extraction_prompt(self, text: str) -> str:
        # Specific to lease contracts
        return self._get_purchase_extraction_prompt(text)

    def _call_qwen_api(self, prompt: str) -> str:
        """Call Qwen API"""
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "qwen-plus",
            "input": {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "result_format": "message",
                "temperature": 0.1  # Low temperature for consistent output
            }
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["output"]["choices"][0]["message"]["content"]
```

**Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/unit/test_ai_extraction.py -v
```

预期: PASS

**Step 5: 实现AI提取Celery任务**

创建 `backend/app/tasks/ai_extraction_tasks.py`:
```python
from celery import shared_task
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.models import Contract, ContractParty, AIExtractionResult
from app.models.enums import ContractStatus, PartyType, PartyTypeDetail
from app.services.ai_extraction_service import AIExtractionService
from app.services.minio_service import MinIOService
from datetime import datetime
import json

@shared_task(name="app.tasks.ai_extraction_tasks.process_ai_extraction")
def process_ai_extraction(contract_id: str):
    """Process AI extraction for a contract"""
    db: Session = SessionLocal()
    ai_service = AIExtractionService()
    minio_service = MinIOService()

    try:
        # Get contract
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Update status
        contract.status = ContractStatus.AI_PROCESSING
        db.commit()

        # Get OCR text
        ocr_text_bytes = minio_service.get_file(contract.ocr_text_path)
        ocr_text = ocr_text_bytes.decode('utf-8')

        # Classify contract type if not already set
        if not contract.contract_type:
            contract.contract_type = ai_service.classify_contract(ocr_text)

        # Extract information
        extracted_data = ai_service.extract_info(ocr_text, contract.contract_type)

        # Process extracted data
        confidence_scores = []

        for field_name, field_data in extracted_data.items():
            if field_data.get("value"):
                # Save to AI extraction results
                extraction_result = AIExtractionResult(
                    contract_id=contract.id,
                    field_name=field_name,
                    raw_value=str(field_data["value"]),
                    reasoning=json.dumps(field_data.get("reasoning", "")),
                    confidence_score=field_data.get("confidence", 0),
                    model_version="qwen-plus"
                )
                db.add(extraction_result)

                confidence_scores.append(field_data.get("confidence", 0))

                # Update contract fields
                if field_name == "total_amount":
                    from decimal import Decimal
                    contract.total_amount = Decimal(field_data["value"])
                elif field_name == "subject_matter":
                    contract.subject_matter = field_data["value"]
                elif field_name == "sign_date":
                    contract.sign_date = datetime.fromisoformat(field_data["value"])
                elif field_name == "effective_date":
                    contract.effective_date = datetime.fromisoformat(field_data["value"])
                elif field_name == "expire_date":
                    contract.expire_date = datetime.fromisoformat(field_data["value"])

                # Handle parties
                elif "party_a" in field_name:
                    party = ContractParty(
                        contract_id=contract.id,
                        party_type=PartyType.PARTY_A,
                        party_name=field_data["value"],
                        confidence_score=field_data.get("confidence", 0)
                    )
                    db.add(party)
                elif "party_b" in field_name:
                    party = ContractParty(
                        contract_id=contract.id,
                        party_type=PartyType.PARTY_B,
                        party_name=field_data["value"],
                        confidence_score=field_data.get("confidence", 0)
                    )
                    db.add(party)

        # Calculate overall confidence
        if confidence_scores:
            contract.confidence_score = sum(confidence_scores) / len(confidence_scores)

        # Determine if review is needed
        # Review needed if any critical field has low confidence
        critical_fields_low_conf = any(
            r.confidence_score < 95
            for r in db.query(AIExtractionResult).filter(
                AIExtractionResult.contract_id == contract.id,
                AIExtractionResult.field_name.in_([
                    "party_a_name", "party_b_name",
                    "total_amount", "sign_date"
                ])
            ).all()
        )

        contract.requires_review = critical_fields_low_conf or contract.confidence_score < 95

        if contract.requires_review:
            contract.status = ContractStatus.PENDING_REVIEW
        else:
            contract.status = ContractStatus.COMPLETED

        db.commit()

        return {"status": "success", "contract_id": contract_id}

    except Exception as e:
        contract.status = ContractStatus.PENDING_AI
        db.commit()
        raise e
    finally:
        db.close()
```

**Step 6: 提交AI提取实现**

```bash
git add backend/app/services/ai_extraction_service.py backend/app/tasks/ai_extraction_tasks.py backend/tests/unit/test_ai_extraction.py
git commit -m "feat: implement AI extraction service and task"
```

---

## Phase 4: 人工审核功能

### Task 4.1: 实现审核API

**Files:**
- Modify: `backend/app/api/contracts.py`
- Create: `backend/app/schemas/review.py`

**Step 1: 创建审核Schema**

创建 `backend/app/schemas/review.py`:
```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReviewRecordCreate(BaseModel):
    contract_id: UUID
    field_name: str
    ai_value: Optional[str] = None
    human_value: str
    reviewer: str
    notes: Optional[str] = None

class ReviewRecordResponse(BaseModel):
    id: UUID
    contract_id: UUID
    field_name: str
    ai_value: Optional[str]
    human_value: str
    reviewer: str
    review_time: datetime
    is_correct: Optional[bool]
    notes: Optional[str]

    class Config:
        from_attributes = True
```

**Step 2: 编写审核API测试**

创建 `backend/tests/integration/test_review_api.py`:
```python
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

def test_submit_review():
    from app.main import app
    client = TestClient(app)

    review_data = {
        "contract_id": "test-contract-id",
        "field_name": "total_amount",
        "ai_value": "100000.00",
        "human_value": "150000.00",
        "reviewer": "test_user"
    }

    response = client.post("/api/contracts/review", json=review_data)

    assert response.status_code == 200
```

**Step 3: 运行测试（预期失败）**

```bash
cd backend
pytest tests/integration/test_review_api.py -v
```

预期: FAIL - review endpoint not implemented

**Step 4: 实现审核API**

在 `backend/app/api/contracts.py` 中添加:
```python
from app.schemas.review import ReviewRecordCreate, ReviewRecordResponse
from app.models.models import ReviewRecord
from app.models.enums import ContractStatus

@router.post("/review", response_model=ReviewRecordResponse)
def submit_review(review_data: ReviewRecordCreate, db: Session = Depends(get_db)):
    """Submit a review record for an AI-extracted field"""

    # Determine if AI was correct
    is_correct = review_data.ai_value == review_data.human_value

    # Create review record
    db_review = ReviewRecord(
        contract_id=review_data.contract_id,
        field_name=review_data.field_name,
        ai_value=review_data.ai_value,
        human_value=review_data.human_value,
        reviewer=review_data.reviewer,
        is_correct=is_correct,
        notes=review_data.notes
    )
    db.add(db_review)

    # Update contract field with human value
    contract = db.query(Contract).filter(Contract.id == review_data.contract_id).first()
    if contract:
        if review_data.field_name == "total_amount":
            from decimal import Decimal
            contract.total_amount = Decimal(review_data.human_value)
        elif review_data.field_name == "party_a_name":
            party = db.query(ContractParty).filter(
                ContractParty.contract_id == contract.id,
                ContractParty.party_type == PartyType.PARTY_A
            ).first()
            if party:
                party.party_name = review_data.human_value

        # Check if all critical fields reviewed
        pending_reviews = db.query(ReviewRecord).filter(
            ReviewRecord.contract_id == contract.id,
            ReviewRecord.field_name.in_([
                "party_a_name", "party_b_name",
                "total_amount", "sign_date"
            ])
        ).count()

        # If all critical fields reviewed, mark as completed
        if pending_reviews >= 4:
            contract.status = ContractStatus.COMPLETED
            contract.requires_review = False

    db.commit()
    db.refresh(db_review)
    return db_review

@router.get("/{contract_id}/reviews", response_model=list[ReviewRecordResponse])
def get_contract_reviews(contract_id: str, db: Session = Depends(get_db)):
    """Get all review records for a contract"""
    reviews = db.query(ReviewRecord).filter(
        ReviewRecord.contract_id == contract_id
    ).all()
    return reviews

@router.get("/pending-review", response_model=list[ContractListResponse])
def get_pending_reviews(db: Session = Depends(get_db)):
    """Get all contracts pending review"""
    contracts = db.query(Contract).filter(
        Contract.status == ContractStatus.PENDING_REVIEW
    ).order_by(Contract.upload_time).all()
    return contracts
```

**Step 5: 运行测试验证通过**

```bash
cd backend
pytest tests/integration/test_review_api.py -v
```

预期: PASS

**Step 6: 提交审核API**

```bash
git add backend/app/api/contracts.py backend/app/schemas/review.py backend/tests/integration/test_review_api.py
git commit -m "feat: implement review API endpoints"
```

---

## Phase 5: 前端开发

### Task 5.1: 初始化Vue3项目

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`

**Step 1: 创建package.json**

创建 `frontend/package.json`:
```json
{
  "name": "contract-scanner-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.3.8",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.4.4",
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.0",
    "typescript": "^5.3.3",
    "vite": "^5.0.4",
    "vue-tsc": "^1.8.25"
  }
}
```

**Step 2: 创建vite配置**

创建 `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

**Step 3: 创建TypeScript配置**

创建 `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Step 4: 创建主应用文件**

创建 `frontend/src/main.ts`:
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
```

创建 `frontend/src/App.vue`:
```vue
<template>
  <el-container style="height: 100vh">
    <el-header>
      <div class="header-content">
        <h1>合同扫描识别系统</h1>
      </div>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
</script>

<style scoped>
.header-content {
  display: flex;
  align-items: center;
  background: #409eff;
  color: white;
  padding: 0 20px;
  height: 100%;
}

h1 {
  margin: 0;
  font-size: 20px;
}
</style>
```

**Step 5: 安装依赖并测试**

```bash
cd frontend
npm install
npm run dev
```

**Step 6: 提交前端初始化**

```bash
git add frontend/
git commit -m "feat: initialize Vue3 frontend project"
```

---

### Task 5.2: 创建合同上传组件

**Files:**
- Create: `frontend/src/views/ContractUpload.vue`
- Create: `frontend/src/api/contract.ts`

**Step 1: 创建API客户端**

创建 `frontend/src/api/contract.ts`:
```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export interface ContractUploadData {
  contract_number: string
  contract_type: string
  file: File
}

export interface Contract {
  id: string
  contract_number: string
  contract_type: string
  status: string
  upload_time: string
  total_amount?: number
  confidence_score?: number
}

export const contractApi = {
  upload: async (data: ContractUploadData) => {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('contract_number', data.contract_number)
    formData.append('contract_type', data.contract_type)

    const response = await api.post('/contracts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  list: async () => {
    const response = await api.get('/contracts/')
    return response.data
  },

  getPendingReviews: async () => {
    const response = await api.get('/contracts/pending-review')
    return response.data
  }
}
```

**Step 2: 创建上传组件**

创建 `frontend/src/views/ContractUpload.vue`:
```vue
<template>
  <el-card class="upload-card">
    <template #header>
      <span>上传合同文件</span>
    </template>

    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
      <el-form-item label="合同编号" prop="contract_number">
        <el-input v-model="form.contract_number" placeholder="请输入合同编号" />
      </el-form-item>

      <el-form-item label="合同类型" prop="contract_type">
        <el-select v-model="form.contract_type" placeholder="请选择合同类型">
          <el-option label="采购合同" value="purchase" />
          <el-option label="销售合同" value="sales" />
          <el-option label="租赁合同" value="lease" />
        </el-select>
      </el-form-item>

      <el-form-item label="合同文件" prop="file">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          accept=".pdf,.docx,.png,.jpg,.jpeg"
        >
          <el-button type="primary">选择文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              支持PDF、Word、图片格式，文件大小不超过10MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitUpload" :loading="uploading">
          上传并识别
        </el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { contractApi } from '@/api/contract'

const formRef = ref()
const uploadRef = ref()
const uploading = ref(false)

const form = reactive({
  contract_number: '',
  contract_type: '',
  file: null as File | null
})

const rules = {
  contract_number: [{ required: true, message: '请输入合同编号', trigger: 'blur' }],
  contract_type: [{ required: true, message: '请选择合同类型', trigger: 'change' }],
  file: [{ required: true, message: '请选择文件', trigger: 'change' }]
}

const handleFileChange = (file: any) => {
  form.file = file.raw
}

const submitUpload = async () => {
  try {
    await formRef.value.validate()

    if (!form.file) {
      ElMessage.error('请选择文件')
      return
    }

    uploading.value = true

    await contractApi.upload({
      contract_number: form.contract_number,
      contract_type: form.contract_type,
      file: form.file
    })

    ElMessage.success('上传成功，正在处理中...')
    resetForm()
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  form.file = null
  uploadRef.value?.clearFiles()
}
</script>

<style scoped>
.upload-card {
  max-width: 600px;
  margin: 0 auto;
}
</style>
```

**Step 3: 提交上传组件**

```bash
git add frontend/src/api/ frontend/src/views/ContractUpload.vue
git commit -m "feat: add contract upload component"
```

---

### Task 5.3: 创建合同列表和审核组件

**Files:**
- Create: `frontend/src/views/ContractList.vue`
- Create: `frontend/src/views/ContractReview.vue`
- Create: `frontend/src/router/index.ts`

**Step 1: 创建路由配置**

创建 `frontend/src/router/index.ts`:
```typescript
import { createRouter, createWebHistory } from 'vue-router'
import ContractUpload from '@/views/ContractUpload.vue'
import ContractList from '@/views/ContractList.vue'
import ContractReview from '@/views/ContractReview.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/upload' },
    { path: '/upload', component: ContractUpload },
    { path: '/contracts', component: ContractList },
    { path: '/review', component: ContractReview }
  ]
})

export default router
```

**Step 2: 创建合同列表组件**

创建 `frontend/src/views/ContractList.vue`:
```vue
<template>
  <el-card>
    <template #header>
      <div class="list-header">
        <span>合同列表</span>
        <el-button @click="$router.push('/upload')">上传新合同</el-button>
      </div>
    </template>

    <el-table :data="contracts" v-loading="loading">
      <el-table-column prop="contract_number" label="合同编号" />
      <el-table-column prop="contract_type" label="类型">
        <template #default="{ row }">
          {{ contractTypeMap[row.contract_type] }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ statusMap[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="upload_time" label="上传时间">
        <template #default="{ row }">
          {{ formatDate(row.upload_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row.id)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { contractApi, type Contract } from '@/api/contract'
import { ElMessage } from 'element-plus'

const contracts = ref<Contract[]>([])
const loading = ref(false)

const contractTypeMap: Record<string, string> = {
  purchase: '采购合同',
  sales: '销售合同',
  lease: '租赁合同'
}

const statusMap: Record<string, string> = {
  pending_ocr: '待OCR',
  ocr_processing: 'OCR处理中',
  pending_ai: '待AI提取',
  ai_processing: 'AI提取中',
  pending_review: '待审核',
  completed: '已完成'
}

const getStatusType = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'pending_review') return 'warning'
  return 'info'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadContracts = async () => {
  loading.value = true
  try {
    contracts.value = await contractApi.list()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const viewDetail = (id: string) => {
  ElMessage.info('详情功能待实现')
}

onMounted(() => {
  loadContracts()
})
</script>

<style scoped>
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

**Step 3: 创建审核组件**

创建 `frontend/src/views/ContractReview.vue`:
```vue
<template>
  <el-card>
    <template #header>
      <span>待审核合同</span>
    </template>

    <el-table :data="pendingContracts" v-loading="loading">
      <el-table-column prop="contract_number" label="合同编号" />
      <el-table-column prop="contract_type" label="类型" />
      <el-table-column prop="confidence_score" label="置信度">
        <template #default="{ row }">
          <el-progress
            :percentage="row.confidence_score || 0"
            :color="getConfidenceColor(row.confidence_score)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="reviewContract(row.id)">
            审核
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { contractApi, type Contract } from '@/api/contract'
import { ElMessage } from 'element-plus'

const pendingContracts = ref<Contract[]>([])
const loading = ref(false)

const getConfidenceColor = (score: number) => {
  if (score >= 95) return '#67c23a'
  if (score >= 80) return '#e6a23c'
  return '#f56c6c'
}

const loadPendingReviews = async () => {
  loading.value = true
  try {
    pendingContracts.value = await contractApi.getPendingReviews()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const reviewContract = (id: string) => {
  ElMessage.info('审核详情功能待实现')
}

onMounted(() => {
  loadPendingReviews()
})
</script>
```

**Step 4: 提交列表和审核组件**

```bash
git add frontend/src/router/ frontend/src/views/ContractList.vue frontend/src/views/ContractReview.vue
git commit -m "feat: add contract list and review components"
```

---

## Phase 6: Docker部署和测试

### Task 6.1: 创建生产Docker配置

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Modify: `docker-compose.prod.yml`

**Step 1: 创建后端Dockerfile**

创建 `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: 创建前端Dockerfile**

创建 `frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

创建 `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 3: 配置生产docker-compose**

编辑 `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: contract_scanner
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7.0-alpine
    restart: always

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    restart: always

  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis
      - minio
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/contract_scanner
      REDIS_URL: redis://redis:6379/0
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
    volumes:
      - ./backend:/app
    restart: always

  celery_worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker -l info -Q ocr,ai
    depends_on:
      - postgres
      - redis
      - minio
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/contract_scanner
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./backend:/app
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
  minio_data:
```

**Step 4: 提交Docker配置**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/nginx.conf docker-compose.prod.yml
git commit -m "feat: add production Docker configuration"
```

---

### Task 6.2: 集成测试

**Files:**
- Create: `backend/tests/integration/test_full_workflow.py`

**Step 1: 编写端到端测试**

创建 `backend/tests/integration/test_full_workflow.py`:
```python
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

def test_full_contract_workflow():
    """Test complete workflow: upload -> OCR -> AI -> review"""
    from app.main import app
    client = TestClient(app)

    # 1. Upload contract
    file_content = b"sample contract content"
    files = {"file": ("contract.pdf", file_content, "application/pdf")}
    data = {
        "contract_number": "TEST001",
        "contract_type": "purchase"
    }

    with patch('app.services.contract_service.MinIOService'):
        response = client.post("/api/contracts/upload", files=files, data=data)
        assert response.status_code == 200
        contract_id = response.json()["id"]

    # 2. Check contract status
    response = client.get(f"/api/contracts/{contract_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending_ocr", "ocr_processing", "pending_ai"]

    # 3. Submit review
    review_data = {
        "contract_id": contract_id,
        "field_name": "total_amount",
        "human_value": "100000.00",
        "reviewer": "test_user"
    }

    response = client.post("/api/contracts/review", json=review_data)
    assert response.status_code == 200
```

**Step 2: 运行集成测试**

```bash
cd backend
pytest tests/integration/test_full_workflow.py -v
```

**Step 3: 提交集成测试**

```bash
git add backend/tests/integration/test_full_workflow.py
git commit -m "test: add end-to-end integration test"
```

---

## Phase 7: 文档和部署

### Task 7.1: 创建部署文档

**Files:**
- Create: `docs/DEPLOYMENT.md`
- Create: `README.md`

**Step 1: 创建部署文档**

创建 `docs/DEPLOYMENT.md`:
```markdown
# 部署指南

## 开发环境

### 启动服务

```bash
# 启动基础设施
docker-compose -f docker-compose.dev.yml up -d

# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Celery worker
celery -A app.tasks.celery_app worker -l info

# 前端
cd frontend
npm install
npm run dev
```

### 访问

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

## 生产环境

### 环境变量

复制 `.env.example` 到 `.env.prod` 并配置：
```env
POSTGRES_PASSWORD=your_secure_password
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=your_secure_password
QWEN_API_KEY=your_qwen_api_key
```

### 部署

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 备份

```bash
# PostgreSQL backup
docker exec postgres pg_dump -U postgres contract_scanner > backup.sql

# MinIO backup (using mc client)
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mirror local/contract-raw /backup/contract-raw
```
```

**Step 2: 创建README**

创建项目根目录 `README.md`:
```markdown
# 历史合同扫描识别系统

自动识别合同关键信息的智能系统。

## 功能

- 支持PDF、Word、图片格式的合同上传
- 自动OCR文本提取
- AI智能提取合同关键信息
- 人工审核确保准确性
- 合同检索和管理

## 技术栈

- 后端: FastAPI + Celery + PostgreSQL + Redis
- 前端: Vue 3 + Element Plus
- 存储: MinIO
- AI: 通义千问/GPT-4

## 快速开始

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看部署文档
cat docs/DEPLOYMENT.md
```

## 许可

MIT License
```

**Step 3: 提交文档**

```bash
git add README.md docs/DEPLOYMENT.md
git commit -m "docs: add deployment and README documentation"
```

---

## 任务完成检查清单

- [ ] Phase 1: 项目初始化完成
  - [ ] 目录结构创建
  - [ ] Docker配置
  - [ ] 数据库模型
  - [ ] MinIO服务
- [ ] Phase 2: 后端API完成
  - [ ] 合同上传API
  - [ ] 合同列表API
  - [ ] 合同详情API
- [ ] Phase 3: OCR和AI完成
  - [ ] OCR处理任务
  - [ ] AI提取任务
  - [ ] 置信度评估
- [ ] Phase 4: 审核功能完成
  - [ ] 审核API
  - [ ] 审核状态管理
- [ ] Phase 5: 前端完成
  - [ ] 上传组件
  - [ ] 列表组件
  - [ ] 审核组件
- [ ] Phase 6: 部署配置完成
  - [ ] Docker配置
  - [ ] 集成测试
- [ ] Phase 7: 文档完成
  - [ ] 部署文档
  - [ ] README

---

## 后续优化

1. 支持更多合同类型（劳动合同、服务合同）
2. 实现合同内容语义搜索
3. 添加合同差异对比功能
4. 集成更多OCR和AI提供商
5. 实现移动端响应式设计
