"""Celery application configuration for async task processing"""

from celery import Celery
from app.core.config import settings

# Create Celery app with Redis broker
celery_app = Celery(
    "contract_scanner",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.ocr_tasks", "app.tasks.ai_extraction_tasks"]
)

# Configure Celery settings
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.tasks.ocr_tasks.process_ocr": {"queue": "ocr"},
        "app.tasks.ai_extraction_tasks.process_ai_extraction": {"queue": "ai_extraction"},
    },

    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Result settings
    result_expires=3600,  # 1 hour
    task_track_started=True,

    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
)

# Optional: Configure task-specific timeouts
celery_app.conf.task_time_limit = 30 * 60  # 30 minutes hard limit
celery_app.conf.task_soft_time_limit = 25 * 60  # 25 minutes soft limit
