from minio import Minio
from app.core.config import settings
import io


class MinIOService:
    """Service for interacting with MinIO object storage"""

    def __init__(self):
        """Initialize MinIO client and ensure buckets exist"""
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self._ensure_buckets_exist()

    def _ensure_buckets_exist(self):
        """Create buckets if they don't exist"""
        for bucket in [settings.minio_bucket_raw, settings.minio_bucket_text]:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    def upload_file(self, content: bytes, filename: str, bucket_type: str = "raw") -> str:
        """
        Upload a file to MinIO

        Args:
            content: File content as bytes
            filename: Name of the file
            bucket_type: Type of bucket ('raw' or 'text')

        Returns:
            File path in format 'bucket/filename'
        """
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
        """
        Get a file from MinIO

        Args:
            file_path: File path in format 'bucket/filename'

        Returns:
            File content as bytes

        Raises:
            ValueError: If file_path format is invalid
            RuntimeError: If file retrieval fails
        """
        try:
            bucket, object_name = file_path.split("/", 1)
        except ValueError:
            raise ValueError(f"Invalid file_path format: {file_path}")

        try:
            response = self.client.get_object(bucket, object_name)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception as e:
            raise RuntimeError(f"Failed to get file {file_path}: {str(e)}") from e

    def delete_file(self, file_path: str):
        """
        Delete a file from MinIO

        Args:
            file_path: File path in format 'bucket/filename'

        Raises:
            ValueError: If file_path format is invalid
            RuntimeError: If file deletion fails
        """
        try:
            bucket, object_name = file_path.split("/", 1)
        except ValueError:
            raise ValueError(f"Invalid file_path format: {file_path}")

        try:
            self.client.remove_object(bucket, object_name)
        except Exception as e:
            raise RuntimeError(f"Failed to delete file {file_path}: {str(e)}") from e
