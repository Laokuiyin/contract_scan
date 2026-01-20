from app.core.config import settings


def test_settings_loaded():
    assert settings.database_url is not None
    assert settings.redis_url is not None
    assert settings.minio_endpoint is not None
