# Contract Scanner - Deployment Guide

## Overview

Contract Scanner is an AI-powered contract analysis system that extracts key information from Chinese contracts using OCR and LLM technologies.

## Table of Contents

- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+
- MinIO (optional, for S3-compatible storage)
- OpenAI API key

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Database Setup

```bash
# Start PostgreSQL (using Docker)
docker run -d \
  --name postgres-dev \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=contract_scanner \
  -p 5432:5432 \
  postgres:16-alpine

# Run migrations
cd backend
alembic upgrade head
```

## Production Deployment

### Using Docker Compose (Recommended)

```bash
# Create environment file
cat > .env << EOF
POSTGRES_DB=contract_scanner
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_minio_password
OPENAI_API_KEY=sk-your-openai-api-key
EOF

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Manual Deployment

#### Backend

```bash
# Build backend image
cd backend
docker build -t contract-scanner-backend:latest .

# Run backend container
docker run -d \
  --name backend \
  -p 8000:8000 \
  --env-file .env \
  contract-scanner-backend:latest
```

#### Frontend

```bash
# Build frontend
cd frontend
npm run build

# Build frontend image
docker build -t contract-scanner-frontend:latest .

# Run frontend container
docker run -d \
  --name frontend \
  -p 80:80 \
  contract-scanner-frontend:latest
```

## Environment Variables

### Backend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Yes | - |
| `REDIS_URL` | Redis connection URL | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key for LLM | Yes | - |
| `MINIO_ENDPOINT` | MinIO endpoint | No | - |
| `MINIO_ACCESS_KEY` | MinIO access key | No | - |
| `MINIO_SECRET_KEY` | MinIO secret key | No | - |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `ALGORITHM` | JWT algorithm | No | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | No | 30 |
| `UPLOAD_DIR` | File upload directory | No | ./uploads |
| `MAX_FILE_SIZE` | Max file size in bytes | No | 10485760 |
| `ALLOWED_EXTENSIONS` | Allowed file extensions | No | pdf,png,jpg |

### Frontend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | Yes | http://localhost:8000 |
| `VITE_APP_TITLE` | Application title | No | Contract Scanner |

## Docker Deployment

### Docker Compose Services

The production Docker Compose setup includes:

1. **PostgreSQL** - Primary database
2. **Redis** - Caching and queue
3. **MinIO** - Object storage
4. **Backend** - FastAPI application
5. **Frontend** - Vue3 static files (Nginx)

### Scaling

```bash
# Scale backend service
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Note: Ensure you have a load balancer (nginx, traefik) in front of scaled services
```

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/api/health

# Check database connection
docker exec -it postgres-dev pg_isready -U postgres

# Check Redis
docker exec -it redis-dev redis-cli ping
```

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs postgres-dev

# Test connection
psql -h localhost -U postgres -d contract_scanner
```

#### OCR Processing Failed

```bash
# Check if Tesseract is installed
tesseract --version

# Install Tesseract (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim

# Install Tesseract (macOS)
brew install tesseract tesseract-lang
```

#### File Upload Errors

```bash
# Check upload directory permissions
ls -la backend/uploads

# Create directory if missing
mkdir -p backend/uploads
chmod 755 backend/uploads
```

#### LLM API Errors

```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Logs

```bash
# Backend logs
docker-compose -f docker-compose.prod.yml logs backend

# Frontend logs
docker-compose -f docker-compose.prod.yml logs frontend

# All logs
docker-compose -f docker-compose.prod.yml logs
```

### Performance Tuning

#### Database

```sql
-- Create indexes for better performance
CREATE INDEX idx_contract_status ON contracts(status);
CREATE INDEX idx_contract_type ON contracts(contract_type);
CREATE INDEX idx_party_contract ON contract_parties(contract_id);
```

#### Redis

```bash
# Set max memory
redis-cli config set maxmemory 1gb
redis-cli config set maxmemory-policy allkeys-lru
```

#### Backend Workers

```bash
# Run with multiple workers (gunicorn)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Monitoring

### Application Monitoring

Consider implementing:

- Prometheus for metrics
- Grafana for visualization
- Sentry for error tracking
- ELK stack for log aggregation

### Database Monitoring

```sql
-- Check table sizes
SELECT
  table_name,
  pg_size_pretty(pg_total_relation_size(table_name::regclass)) as size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(table_name::regclass) DESC;

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Security Considerations

1. **Change default passwords** in production
2. **Use HTTPS** in production (Let's Encrypt recommended)
3. **Restrict CORS** to specific origins
4. **Enable rate limiting** on API endpoints
5. **Regular security updates**: `docker-compose pull && docker-compose up -d`
6. **Backup database**: Regular pg_dump backups
7. **Secure file storage**: Use encryption for sensitive documents

## Backup and Recovery

### Database Backup

```bash
# Backup
docker exec postgres-dev pg_dump -U postgres contract_scanner > backup.sql

# Restore
docker exec -i postgres-dev psql -U postgres contract_scanner < backup.sql
```

### File Storage Backup

```bash
# Backup MinIO data
docker run --rm -v minio_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/minio-backup.tar.gz -C /data .
```

## Support

For issues and questions:
- GitHub Issues: [repository URL]
- Documentation: [docs URL]
- Email: support@example.com
