# 历史合同扫描识别系统 - 设计文档

**设计日期**: 2025-01-20
**项目类型**: 全新独立项目
**目标用户**: 企业内部部门
**部署方式**: 混合部署（本地私有化 + 云端API服务）

## 1. 项目概述

开发一个历史合同扫描识别系统，支持上传合同图片/PDF/Office文档，通过OCR和AI技术自动识别合同内容，提取结构化关键信息，并通过人工审核机制确保关键信息100%准确。

**核心需求**:
- 支持采购合同、销售合同、租赁合同三种类型
- 提取字段：甲方/乙方信息、合同类型、合同金额、标的物、合同日期
- 关键信息保真：金额、日期、主体信息必须准确
- 便于后续检索和查询

## 2. 系统架构

### 2.1 整体架构

采用**分层微服务架构**:

**接入层**:
- Nginx反向代理，处理HTTPS和负载均衡
- 部署在内网DMZ区，对外提供Web访问

**应用层**:
- **API服务**: FastAPI实现，提供RESTful接口
- **任务处理服务**: Celery + Redis，异步处理OCR和AI提取任务
- **审核服务**: 独立的审核流程管理模块

**AI服务层**:
- OCR服务: 调用百度/腾讯云API（图片） + pdfplumber（PDF）
- AI提取服务: OpenAI API 或通义千问
- 置信度评估模块: 对每个提取字段计算置信度分数

**存储层**:
- PostgreSQL: 存储合同结构化数据和审核记录
- MinIO: 存储原始文件和处理的中间文件（如OCR文本）
- Redis: 任务队列和缓存

### 2.2 核心数据流程

1. **上传阶段**: 用户通过Web界面上传合同文件，系统生成唯一任务ID，存入MinIO原始文件桶

2. **OCR识别**:
   - 根据文件类型路由: 图片→云端OCR API，PDF→pdfplumber提取，Office→python-docx解析
   - 提取的纯文本存入MinIO文本桶，供后续AI使用

3. **AI提取**:
   - 首先调用分类模型判断合同类型（采购/销售/租赁）
   - 然后使用对应类型的专门Prompt提取结构化字段
   - 对每个字段计算置信度（基于AI返回的reasoning + 规则校验）

4. **人工审核**（关键）:
   - 置信度<95%的字段自动进入待审核队列
   - 关键字段（甲方/乙方/金额/日期）无论置信度都需要复核
   - 审核人员可修正AI提取结果，修正数据用于后续模型微调

5. **完成入库**: 审核通过后数据写入PostgreSQL正式表，更新检索索引

## 3. 数据库设计

### 3.1 核心表结构

**contracts（合同主表）**:
```
- id: UUID主键
- contract_number: 合同编号（唯一索引）
- contract_type: 合同类型（枚举:采购/销售/租赁）
- file_path: 原始文件在MinIO的路径
- ocr_text_path: OCR提取文本的路径
- status: 处理状态（待OCR/OCR中/待AI提取/提取中/待审核/已完成）
- upload_time: 上传时间
- created_by: 上传用户
- total_amount: 合同金额(decimal)
- subject_matter: 合同标的物(text)
- sign_date: 签订日期
- effective_date: 生效日期
- expire_date: 到期日期
- confidence_score: 综合置信度(0-100)
- requires_review: 是否需要人工审核(boolean)
```

**contract_parties（合同主体表）**:
```
- id: UUID主键
- contract_id: 外键关联contracts
- party_type: 主体类型(甲方/乙方)
- party_name: 名称
- party_type_detail: 主体性质(公司/个人/政府机构)
- tax_number: 税号
- legal_representative: 法定代表人
- address: 地址
- contact_info: 联系方式(JSON)
- confidence_score: 该字段的置信度
```

**ai_extraction_results（AI提取结果详情表）**:
```
- id: UUID主键
- contract_id: 外键
- field_name: 字段名(如party_a_name/total_amount)
- raw_value: AI提取的原始值
- reasoning: AI的推理过程(JSON,存储用于优化)
- confidence_score: 置信度分数
- model_version: 使用的AI模型版本
- prompt_template: 使用的提示词模板
- extract_time: 提取时间
```

**review_records（人工审核记录表）**:
```
- id: UUID主键
- contract_id: 外键
- field_name: 审核的字段
- ai_value: AI提取的值
- human_value: 人工修正的值
- reviewer: 审核人
- review_time: 审核时间
- is_correct: AI是否正确(用于后续模型优化)
- notes: 备注说明
```

**payment_terms（付款条款表）**（可选）:
```
- id: UUID主键
- contract_id: 外键
- payment_stage: 付款阶段(如首付/尾款)
- payment_ratio: 付款比例
- payment_amount: 付款金额
- payment_condition: 付款条件
- due_date: 应付日期
```

### 3.2 索引策略

- contract_number建立唯一索引（防止重复上传）
- status建立普通索引（便于查询待处理任务）
- contract_type + sign_date建立复合索引（便于按类型和时间检索）
- confidence_score建立索引（便于筛选低置信度记录）

## 4. AI提取策略

### 4.1 两阶段提取

**阶段1: 合同分类**

使用专门的分类Prompt判断合同类型：

```
你是一个合同分类专家。请根据以下合同文本,判断合同类型。

合同类型:
- 采购合同: 买方购买商品或服务的合同
- 销售合同: 卖方出售商品或合同的合同
- 租赁合同: 关于房屋、设备等租赁的合同

合同文本:
{contract_text}

请只返回合同类型(采购合同/销售合同/租赁合同),不要其他内容。
```

**阶段2: 结构化信息提取**

根据不同合同类型使用专门的Prompt。以**采购合同**为例:

```
你是一个合同信息提取专家。请从以下采购合同中提取关键信息,并以JSON格式返回。

合同文本:
{contract_text}

请提取以下字段:
1. 合同编号: 查找"合同编号"、"协议编号"等关键词
2. 甲方(采购方): 公司名称、税号、法定代表人、地址、联系方式
3. 乙方(供应商): 公司名称、税号、法定代表人、地址、联系方式
4. 合同金额: 数字金额和大写金额,需要验证两者一致
5. 合同标的物: 采购的物品/服务名称、规格、数量
6. 签订日期: 格式为YYYY-MM-DD
7. 生效日期: 格式为YYYY-MM-DD
8. 到期日期: 格式为YYYY-MM-DD
9. 付款方式: 如"分期付款"、"一次性付款"等

返回格式:
{
  "contract_number": {"value": "提取值", "confidence": 0-95, "reasoning": "在第一页找到'合同编号:HT2024001'"},
  "party_a": {...},
  ...
}

注意:
- confidence字段表示置信度(0-100),基于文本明确程度
- 如果找不到某个字段,value设为null,confidence设为0
- 金额必须找到明确数字,不要推测
- 日期必须完整,找不到则返回null
```

### 4.2 置信度计算

**自动规则校验**（降低AI过信任）:
1. **金额字段**: 数字和大写金额不一致 → 置信度强制降至70%
2. **日期字段**: 格式不规范或缺失 → 置信度不超过80%
3. **公司名称**: 找不到税号佐证 → 置信度不超过85%
4. **合同编号**: 格式明显不标准 → 置信度不超过75%

**AI置信度加权**:
- 最终置信度 = AI置信度 × 0.7 + 规则校验分数 × 0.3
- 例如: AI说95%,但缺少税号佐证 → 95×0.7 + 85×0.3 = 92%

### 4.3 模型选择

- **首选**: 通义千问-Plus（qwen-plus）- 中文理解好，价格合理（约¥0.008/1K tokens）
- **备选**: GPT-4o-mini - 复杂合同时使用，价格略高但准确率更高
- **本地小模型**（可选）: Qwen-7B-Instruct，用于简单合同预筛选

## 5. 人工审核工作流

### 5.1 审核触发机制

**自动触发规则**:
1. **硬性要求**（无条件审核）:
   - 甲方/乙方名称
   - 合同金额
   - 签订/生效/到期日期

2. **置信度触发**:
   - 任意字段置信度 < 95%
   - 金额字段置信度 < 90%（更严格）

3. **规则校验失败**:
   - 数字金额与大写金额不一致
   - 日期缺失或不完整
   - 合同编号格式异常

### 5.2 审核界面设计

**待审核队列页面**:
- 左侧: 待审核合同列表（按优先级排序）
- 右侧: 审核工作区（原文档 + 提取结果表单）

### 5.3 审核操作流程

1. **确认**: 审核人员检查AI提取结果
   - 正确 → 点击"确认"
   - 错误 → 手动修改，系统记录修正值

2. **批量操作**: 全部确认/全部拒绝

3. **完成审核**: 所有关键字段审核通过 → 合同状态变更为"已完成"

### 5.4 审核权限管理

- **普通审核员**: 只能审核自己部门上传的合同
- **高级审核员**: 可审核所有合同，可批量确认
- **管理员**: 可查看所有审核记录，可修正已审核数据

### 5.5 质量保证

- **抽检制度**: 每日随机抽取5%已审核合同进行二次审核
- **AI反馈学习**: 积累修正数据用于优化Prompt和模型微调

## 6. 技术栈

### 6.1 后端

- **FastAPI 0.104+**: 高性能异步API框架
- **Python 3.11**: 最新类型注解和性能优化
- **SQLAlchemy 2.0**: ORM框架
- **Celery 5.3+**: 分布式任务队列
- **Redis 7.0**: 消息代理和缓存
- **PostgreSQL 16**: 主数据库
- **MinIO**: 对象存储

### 6.2 前端

- **Vue 3.3+**: Composition API
- **Vite 5.0**: 构建工具
- **Element Plus**: UI组件库
- **Pinia**: 状态管理
- **TypeScript**: 类型安全

## 7. 部署方案

### 7.1 开发环境

使用Docker Compose本地开发，包含：
- PostgreSQL + Redis + MinIO
- API服务 + Celery Worker
- 前端开发服务器（热重载）

启动方式: `docker-compose -f docker-compose.dev.yml up -d`

### 7.2 生产环境

云服务器部署（阿里云/腾讯云）:
1. 安装Docker和Docker Compose
2. 配置`.env.prod`环境变量
3. `docker-compose -f docker-compose.prod.yml up -d`
4. 配置Nginx SSL证书

### 7.3 数据备份

- PostgreSQL: 每日自动备份到云盘
- MinIO: 开启版本控制，定期快照

## 8. 项目目录结构

```
contract-scanner/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── models/        # SQLAlchemy模型
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # 业务逻辑
│   │   ├── tasks/         # Celery任务
│   │   └── main.py        # FastAPI应用
│   ├── tests/             # 测试
│   ├── alembic/           # 数据库迁移
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # Vue组件
│   │   ├── views/         # 页面
│   │   └── main.ts
│   └── vite.config.ts
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── .env.example
```

## 9. 后续优化方向

1. **支持更多合同类型**: 劳动合同、服务合同等
2. **智能检索**: 基于合同内容的语义搜索
3. **合同对比**: 比对相似合同的差异
4. **风险预警**: 识别异常条款（如霸王条款）
5. **数据统计**: 合同金额趋势、供应商分析等
