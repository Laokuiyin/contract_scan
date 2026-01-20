"""Basic tests for Celery configuration"""

import pytest
from app.tasks.celery_app import celery_app


class TestCeleryConfig:
    """Test Celery app configuration"""

    def test_celery_app_exists(self):
        """Test that Celery app is initialized"""
        assert celery_app is not None
        assert celery_app.main == "contract_scanner"

    def test_celery_broker_configured(self):
        """Test that broker is configured"""
        assert celery_app.conf.broker_url is not None
        assert "redis" in celery_app.conf.broker_url

    def test_celery_backend_configured(self):
        """Test that result backend is configured"""
        assert celery_app.conf.result_backend is not None
        assert "redis" in celery_app.conf.result_backend

    def test_task_routes_configured(self):
        """Test that task routing is configured"""
        routes = celery_app.conf.task_routes
        assert "app.tasks.ocr_tasks.process_ocr" in routes
        assert "app.tasks.ai_extraction_tasks.process_ai_extraction" in routes
        assert routes["app.tasks.ocr_tasks.process_ocr"]["queue"] == "ocr"
        assert routes["app.tasks.ai_extraction_tasks.process_ai_extraction"]["queue"] == "ai_extraction"

    def test_task_serialization_configured(self):
        """Test that task serialization is configured"""
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert "json" in celery_app.conf.accept_content
