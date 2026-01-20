# Contract Scanner

An AI-powered contract analysis system that automatically extracts and verifies key information from Chinese contracts using OCR and Large Language Models (LLM).

## Features

- **Intelligent OCR**: Advanced text extraction from contract images/PDFs using Tesseract OCR
- **AI-Powered Extraction**: Leverages GPT models to extract structured contract data
- **Multi-Contract Support**: Supports sales, purchase, service, and employment contracts
- **Human-in-the-Loop Review**: Built-in review workflow for data verification
- **RESTful API**: Clean FastAPI backend with comprehensive endpoints
- **Modern Frontend**: Vue3 + TypeScript + Element Plus UI
- **Docker Ready**: Production-ready Docker Compose configuration

## Architecture

```
contract_scan/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration, database
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── tests/           # Backend tests
│   └── alembic/         # Database migrations
├── frontend/            # Vue3 application
│   └── src/
│       ├── api/        # API clients
│       ├── components/  # Vue components
│       ├── views/       # Page components
│       └── router/      # Vue Router config
├── docs/                # Documentation
└── docker-compose.yml   # Docker orchestration
```

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Relational database
- **Redis**: Caching and task queue
- **Alembic**: Database migration tool
- **Tesseract OCR**: Optical character recognition
- **OpenAI GPT**: Contract information extraction
- **Pydantic**: Data validation using Python type annotations

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **TypeScript**: Type-safe JavaScript
- **Element Plus**: Vue 3 UI library
- **Pinia**: State management
- **Vue Router**: Official router for Vue.js
- **Vite**: Next generation frontend tooling

### Infrastructure
- **Docker**: Container platform
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and static file serving
- **MinIO**: S3-compatible object storage

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### 1. Clone the Repository

```bash
git clone <repository-url>
cd contract_scan
```

### 2. Configure Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
POSTGRES_DB=contract_scanner
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# MinIO (optional)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_minio_password
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Redis, MinIO, Backend, Frontend)
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Integration tests
pytest tests/integration/ -v
```

## API Endpoints

### Contracts

- `POST /api/contracts/upload` - Upload a new contract
- `GET /api/contracts/` - List all contracts
- `GET /api/contracts/{id}` - Get contract details
- `GET /api/contracts/pending-review` - Get contracts pending review

### Reviews

- `POST /api/contracts/review` - Create a review record
- `GET /api/contracts/{id}/reviews` - Get contract reviews

### Health

- `GET /api/health` - Health check endpoint

For complete API documentation, visit `/docs` when the backend is running.

## Database Schema

### Key Tables

- **contracts**: Contract metadata and extracted information
- **contract_parties**: Contract parties (buyer, seller, etc.)
- **ai_extraction_results**: AI extraction results with confidence scores
- **review_records**: Human review and verification records

## Workflow

1. **Upload**: User uploads contract document (PDF/image)
2. **OCR Processing**: System extracts text using Tesseract OCR
3. **AI Extraction**: OpenAI GPT extracts structured information:
   - Contract number
   - Parties (buyer, seller, etc.)
   - Total amount
   - Dates (sign date, effective date, expiry date)
   - Subject matter
4. **Human Review**: Reviewer verifies and corrects extracted data
5. **Completion**: Contract marked as reviewed and approved

## Configuration

### Backend Configuration (`backend/app/core/config.py`)

```python
# Database settings
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

# OCR settings
TESSERACT_PATH = "/usr/bin/tesseract"
UPLOAD_DIR = "./uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# OpenAI settings
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4-vision-preview"
```

### Frontend Configuration (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Contract Scanner
```

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](docs/DEPLOYMENT.md).

### Production Deployment

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service health
curl http://localhost:8000/api/health
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

### Unit Tests

```bash
cd backend
pytest tests/unit/ -v
```

### Integration Tests

```bash
cd backend
pytest tests/integration/ -v
```

### End-to-End Tests

```bash
# Requires running services
pytest tests/e2e/ -v
```

## Troubleshooting

### OCR Issues

If OCR fails to extract Chinese text:
1. Ensure Tesseract Chinese language pack is installed:
   ```bash
   brew install tesseract-lang  # macOS
   apt-get install tesseract-ocr-chi-sim  # Ubuntu
   ```
2. Verify Tesseract path in configuration

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# View logs
docker logs postgres-dev

# Restart service
docker-compose restart postgres
```

### LLM API Issues

- Verify API key is set correctly
- Check OpenAI API status
- Review rate limits and quotas

## License

This project is licensed under the MIT License.

## Support

For questions or issues:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review API docs at `/docs` endpoint

## Roadmap

- [ ] Support for more contract types
- [ ] Batch contract processing
- [ ] Advanced analytics dashboard
- [ ] Contract template matching
- [ ] Multi-language support
- [ ] Export to Excel/PDF reports
- [ ] Integration with document signing services

## Acknowledgments

- Tesseract OCR community
- OpenAI for GPT models
- FastAPI and Vue.js communities
