import pytest
from unittest.mock import Mock, patch, MagicMock
import io


@patch('app.services.minio_service.Minio')
def test_minio_service_init(mock_minio_class):
    """Test MinIO service initialization"""
    with patch('app.services.minio_service.settings') as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_raw = "contract-raw"
        mock_settings.minio_bucket_text = "contract-text"

        from app.services.minio_service import MinIOService

        mock_client = Mock()
        mock_minio_class.return_value = mock_client

        service = MinIOService()

        # Verify Minio client was created with correct parameters
        mock_minio_class.assert_called_once_with(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )

        # Verify buckets are created
        assert mock_client.bucket_exists.call_count == 2


@patch('app.services.minio_service.Minio')
def test_minio_service_upload_file_raw(mock_minio_class):
    """Test uploading a file to raw bucket"""
    with patch('app.services.minio_service.settings') as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_raw = "contract-raw"
        mock_settings.minio_bucket_text = "contract-text"

        from app.services.minio_service import MinIOService

        mock_client = Mock()
        mock_minio_class.return_value = mock_client

        service = MinIOService()

        # Test upload to raw bucket
        file_path = service.upload_file(b"test content", "test.pdf", "raw")

        assert file_path == "contract-raw/test.pdf"
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args

        assert call_args[0][0] == "contract-raw"
        assert call_args[0][1] == "test.pdf"
        assert isinstance(call_args[0][2], io.BytesIO)


@patch('app.services.minio_service.Minio')
def test_minio_service_upload_file_text(mock_minio_class):
    """Test uploading a file to text bucket"""
    with patch('app.services.minio_service.settings') as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_raw = "contract-raw"
        mock_settings.minio_bucket_text = "contract-text"

        from app.services.minio_service import MinIOService

        mock_client = Mock()
        mock_minio_class.return_value = mock_client

        service = MinIOService()

        # Test upload to text bucket
        file_path = service.upload_file(b"extracted text", "test.txt", "text")

        assert file_path == "contract-text/test.txt"
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args

        assert call_args[0][0] == "contract-text"
        assert call_args[0][1] == "test.txt"


@patch('app.services.minio_service.Minio')
def test_minio_service_get_file(mock_minio_class):
    """Test getting a file from MinIO"""
    with patch('app.services.minio_service.settings') as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_raw = "contract-raw"
        mock_settings.minio_bucket_text = "contract-text"

        from app.services.minio_service import MinIOService

        mock_client = Mock()
        mock_minio_class.return_value = mock_client

        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = b"file content"
        mock_client.get_object.return_value = mock_response

        service = MinIOService()

        # Test get file
        content = service.get_file("contract-raw/test.pdf")

        mock_client.get_object.assert_called_once_with("contract-raw", "test.pdf")
        assert content == b"file content"


@patch('app.services.minio_service.Minio')
def test_minio_service_delete_file(mock_minio_class):
    """Test deleting a file from MinIO"""
    with patch('app.services.minio_service.settings') as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_raw = "contract-raw"
        mock_settings.minio_bucket_text = "contract-text"

        from app.services.minio_service import MinIOService

        mock_client = Mock()
        mock_minio_class.return_value = mock_client

        service = MinIOService()

        # Test delete file
        service.delete_file("contract-raw/test.pdf")

        mock_client.remove_object.assert_called_once_with("contract-raw", "test.pdf")


@patch('app.services.minio_service.Minio')
def test_minio_service_buckets_exist(mock_minio_class):
    """Test that buckets are created if they don't exist"""
    with patch('app.services.minio_service.settings') as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_raw = "contract-raw"
        mock_settings.minio_bucket_text = "contract-text"

        from app.services.minio_service import MinIOService

        mock_client = Mock()
        mock_client.bucket_exists.return_value = False
        mock_minio_class.return_value = mock_client

        service = MinIOService()

        # Verify make_bucket was called for both buckets
        assert mock_client.make_bucket.call_count == 2
        mock_client.make_bucket.assert_any_call("contract-raw")
        mock_client.make_bucket.assert_any_call("contract-text")
