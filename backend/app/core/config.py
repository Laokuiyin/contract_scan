from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_RAW: str = "contract-raw"
    MINIO_BUCKET_TEXT: str = "contract-text"
    MINIO_SECURE: bool = False

    # AI Services
    AI_PROVIDER: str = "qwen"
    QWEN_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # OCR
    OCR_PROVIDER: str = "baidu"
    BAIDU_OCR_API_KEY: str = ""
    BAIDU_OCR_SECRET_KEY: str = ""

    # Security
    SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Property aliases for backward compatibility
    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    @property
    def minio_endpoint(self) -> str:
        return self.MINIO_ENDPOINT

    @property
    def minio_access_key(self) -> str:
        return self.MINIO_ACCESS_KEY

    @property
    def minio_secret_key(self) -> str:
        return self.MINIO_SECRET_KEY

    @property
    def minio_bucket_raw(self) -> str:
        return self.MINIO_BUCKET_RAW

    @property
    def minio_bucket_text(self) -> str:
        return self.MINIO_BUCKET_TEXT

    @property
    def minio_secure(self) -> bool:
        return self.MINIO_SECURE

    @property
    def ai_provider(self) -> str:
        return self.AI_PROVIDER

    @property
    def qwen_api_key(self) -> str:
        return self.QWEN_API_KEY

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def ocr_provider(self) -> str:
        return self.OCR_PROVIDER

    @property
    def baidu_ocr_api_key(self) -> str:
        return self.BAIDU_OCR_API_KEY

    @property
    def baidu_ocr_secret_key(self) -> str:
        return self.BAIDU_OCR_SECRET_KEY

    @property
    def secret_key(self) -> str:
        return self.SECRET_KEY


settings = Settings()
