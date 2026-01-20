# Contract Scanner

合同扫描识别系统 - 一个基于 AI 的智能合同分析系统，支持自动提取和验证中文合同的关键信息。

## 功能特性

### 核心功能
- **📑 多文件上传**: 支持一次上传多个图片/PDF，自动归并为同一合同
- **🔍 智能 OCR**: 使用百度 OCR 高精度接口进行文字识别
- **🤖 AI 提取**: 集成通义千问（Qwen）大模型提取结构化合同数据
- **⚡ 自动识别**: 上传后自动触发 OCR 和 AI 提取，无需手动操作
- **📊 任务队列**: 智能队列管理，顺序处理识别任务，避免资源冲突
- **📄 文件管理**: 在线查看原始文件，支持下载和删除
- **✅ 人工审核**: 内置审核工作流程，支持人工验证和修正
- **🗑️ 批量删除**: 支持批量选择删除合同

### 提取信息
- 合同编号
- 甲方名称、乙方名称
- 合同金额
- 签署日期、生效日期、到期日期
- 合同标的物
- 置信度评分

## 技术架构

```
contract_scan/
├── backend/              # FastAPI 后端应用
│   ├── app/
│   │   ├── api/         # API 端点
│   │   │   └── contracts.py  # 合同相关 API
│   │   ├── core/        # 配置、数据库连接
│   │   ├── models/      # SQLAlchemy 数据模型
│   │   │   ├── models.py       # 合同、参与方、文件模型
│   │   │   └── enums.py        # 枚举定义
│   │   ├── schemas/     # Pydantic 数据验证模式
│   │   ├── services/    # 业务逻辑
│   │   │   ├── ocr_service.py     # OCR 服务（百度 OCR）
│   │   │   ├── ai_extraction_service.py  # AI 提取服务（Qwen）
│   │   │   ├── ocr_queue.py       # OCR 任务队列管理
│   │   │   └── contract_service.py # 合同服务
│   │   └── tasks/       # 后台任务
│   │       ├── ocr_tasks.py       # OCR 处理任务
│   │       └── ai_extraction_tasks.py  # AI 提取任务
│   ├── alembic/         # 数据库迁移
│   └── tests/           # 测试
├── frontend/            # Vue3 前端应用
│   └── src/
│       ├── api/        # API 客户端
│       ├── components/ # Vue 组件
│       │   └── NavBar.vue
│       ├── views/      # 页面组件
│       │   ├── ContractList.vue    # 合同列表
│       │   ├── ContractUpload.vue  # 合同上传
│       │   └── ContractDetail.vue  # 合同详情
│       └── router/     # Vue Router 配置
└── docs/               # 文档
```

## 技术栈

### 后端
- **FastAPI**: 现代化 Python Web 框架
- **SQLAlchemy**: ORM 和 SQL 工具包
- **PostgreSQL**: 关系型数据库
- **Redis**: 缓存和任务队列
- **Alembic**: 数据库迁移工具
- **百度 OCR**: 高精度 OCR 识别
- **通义千问 (Qwen)**: 阿里云大语言模型
- **Pydantic**: 数据验证

### 前端
- **Vue 3**: 渐进式 JavaScript 框架
- **TypeScript**: 类型安全的 JavaScript
- **Element Plus**: Vue 3 UI 组件库
- **Vite**: 新一代前端构建工具
- **Vue Router**: 官方路由
- **Axios**: HTTP 客户端

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 6+
- 百度 OCR API Key
- 通义千问 API Key

### 1. 克隆仓库

```bash
git clone <repository-url>
cd contract_scan
```

### 2. 配置环境变量

创建后端配置文件 `backend/.env`:

```env
# 数据库
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/contract_scanner

# Redis
REDIS_URL=redis://localhost:6379/0

# 百度 OCR
BAIDU_OCR_API_KEY=your_baidu_api_key
BAIDU_OCR_SECRET_KEY=your_baidu_secret_key

# 通义千问
QWEN_API_KEY=your_qwen_api_key
```

### 3. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 5. 访问应用

- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs

## 工作流程

### 完整流程

```
1. 上传文件
   ├─ 选择合同编号（如：111）
   ├─ 选择合同类型（销售/采购/服务/劳动）
   └─ 选择多个文件（图片/PDF）

2. 自动创建合同
   ├─ 创建一个合同记录
   ├─ 保存所有文件并编号（0, 1, 2...）
   └─ 自动加入 OCR 识别队列

3. OCR 识别（队列处理）
   ├─ 按顺序处理每个合同
   ├─ 对每个文件按顺序进行 OCR
   ├─ 合并所有文本（分隔：=== 下一页 ===）
   └─ 保存为 {合同编号}_ocr.txt

4. AI 提取（自动触发）
   ├─ 读取 OCR 识别的文本
   ├─ 调用通义千问 API 提取信息：
   │  ├─ 甲方名称
   │  ├─ 乙方名称
   │  ├─ 合同金额
   │  ├─ 签署日期、生效日期、到期日期
   │  └─ 合同标的物
   ├─ 保存到数据库
   └─ 更新合同状态为"已完成"

5. 查看结果
   ├─ 合同列表显示：
   │  ├─ 甲方名称
   │  ├─ 乙方名称
   │  └─ 合同金额
   └─ 合同详情显示：
   │  ├─ 基本信息
   │  ├─ 提取信息
   │  ├─ OCR 识别结果
   │  └─ 原始文件列表
```

### 任务队列机制

- **单线程处理**: 每次只处理一个合同的识别任务
- **自动排队**: 新任务自动加入队列等待
- **失败继续**: 任务失败后自动处理下一个
- **状态反馈**: 实时显示当前处理状态

## API 端点

### 合同管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/contracts/upload` | 上传合同（支持多文件） |
| GET | `/api/contracts/` | 获取合同列表 |
| GET | `/api/contracts/{id}` | 获取合同详情 |
| DELETE | `/api/contracts/{id}` | 删除单个合同 |
| POST | `/api/contracts/batch-delete` | 批量删除合同 |
| GET | `/api/contracts/pending-review` | 获取待审核合同 |

### OCR 和识别

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/contracts/{id}/ocr` | 触发 OCR 识别 |
| GET | `/api/contracts/{id}/ocr-text` | 获取 OCR 识别文本 |

### 文件管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/contracts/{id}/files` | 获取合同文件列表 |
| GET | `/api/contracts/files/{id}/download` | 下载/查看文件 |
| DELETE | `/api/contracts/{id}/files/{file_id}` | 删除文件 |

### 审核

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/contracts/review` | 创建审核记录 |
| GET | `/api/contracts/{id}/reviews` | 获取审核记录 |

## 数据库模型

### 主要表结构

**contracts** - 合同表
- 合同编号、类型、状态
- 文件路径、OCR 文本路径
- 提取字段：金额、标的、日期
- 置信度评分

**contract_files** - 合同文件表
- 关联合同 ID
- 文件路径、文件名
- 文件顺序（用于多页合同）

**contract_parties** - 合同参与方表
- 关联合同 ID
- 参与方类型（甲方/乙方）
- 参与方名称、税号等

**ai_extraction_results** - AI 提取结果表
- 关联合同 ID
- 字段名、原始值、推理过程
- 置信度评分

**review_records** - 审核记录表
- 关联合同 ID
- AI 值、人工修正值
- 审核人、是否正确

## 配置说明

### 后端配置 (`backend/app/core/config.py`)

```python
# 百度 OCR
BAIDU_OCR_API_KEY = "your_api_key"
BAIDU_OCR_SECRET_KEY = "your_secret_key"

# 通义千问
QWEN_API_KEY = "your_qwen_api_key"
QWEN_MODEL = "qwen-plus"  # 或 qwen-turbo

# 文件上传
UPLOAD_DIR = "./uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']

# OCR 队列
OCR_QUEUE_WORKERS = 1  # 队列工作线程数
```

### 前端配置 (`frontend/.env`)

```env
VITE_API_BASE_URL=/api
```

## 部署

详细的部署说明请参考 [DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Docker 部署

```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 生产环境

```bash
# 构建前端
cd frontend
npm run build

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d
```

## 测试

### 后端测试

```bash
cd backend

# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/ -v

# 测试覆盖率
pytest --cov=app --cov-report=html
```

### 前端测试

```bash
cd frontend

# 单元测试
npm run test

# 类型检查
npm run type-check

# 构建
npm run build
```

## 常见问题

### OCR 识别失败

1. 检查百度 OCR API Key 是否正确
2. 确认 API 额度是否充足
3. 查看后端日志获取详细错误信息

### AI 提取不准确

1. OCR 识别质量直接影响 AI 提取
2. 确保上传的图片清晰、完整
3. 尝试使用更高分辨率的图片
4. 人工审核和修正提取结果

### 文件上传失败

1. 检查文件大小是否超过限制（50MB）
2. 确认文件格式是否支持（PDF/JPG/PNG）
3. 查看后端日志获取详细错误信息

### 任务队列卡住

1. 查看后端日志确认队列工作线程状态
2. 重启后端服务
3. 检查是否有任务一直失败导致队列阻塞

## 路线图

- [ ] 支持更多合同类型模板
- [ ] OCR 识别结果手动编辑
- [ ] 批量导出合同信息到 Excel
- [ ] 合同模板匹配和自动分类
- [ ] 高级数据分析仪表板
- [ ] 与电子签名服务集成
- [ ] 多语言支持

## 贡献指南

欢迎贡献代码！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 致谢

- 百度 OCR 团队
- 阿里云通义千问团队
- FastAPI 和 Vue.js 社区

## 联系方式

如有问题或建议，请：
- 在 GitHub 上提 Issue
- 查看项目文档 `/docs`
- 访问 API 文档 `/docs` 端点
