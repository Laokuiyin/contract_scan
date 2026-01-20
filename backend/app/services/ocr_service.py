"""OCR service for extracting text from documents"""

import io
import tempfile
import os
from typing import Optional
from paddleocr import PaddleOCR
from pdfplumber import PDF
from docx import Document
from app.services.minio_service import MinIOService
from app.core.config import settings


class OCRService:
    """Service for OCR text extraction from PDF, images, and DOCX files"""

    def __init__(self):
        """Initialize OCR service with PaddleOCR"""
        self.minio = MinIOService()
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text from a file stored in MinIO

        Args:
            file_path: MinIO file path (bucket/filename)

        Returns:
            Extracted text content
        """
        # Download file from MinIO
        file_content = self.minio.get_file(file_path)

        # Get file extension
        filename = file_path.split("/")[-1]
        ext = os.path.splitext(filename)[1].lower()

        # Extract text based on file type
        if ext == '.pdf':
            return self._extract_from_pdf(file_content)
        elif ext in ['.png', '.jpg', '.jpeg']:
            return self._extract_from_image(file_content)
        elif ext == '.docx':
            return self._extract_from_docx(file_content)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF using pdfplumber for text and OCR for images"""
        text_parts = []

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            with PDF.open(tmp_path) as pdf:
                for page in pdf.pages:
                    # Try to extract text directly first
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(text)
                    else:
                        # If no text, try OCR on page image
                        try:
                            img = page.to_image()
                            ocr_result = self.ocr.ocr(img.original, cls=True)
                            if ocr_result and ocr_result[0]:
                                page_text = '\n'.join([line[1][0] for line in ocr_result[0] if line[1]])
                                text_parts.append(page_text)
                        except Exception:
                            pass
        finally:
            os.unlink(tmp_path)

        return '\n\n'.join(text_parts)

    def _extract_from_image(self, content: bytes) -> str:
        """Extract text from image using PaddleOCR"""
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = self.ocr.ocr(tmp_path, cls=True)
            if result and result[0]:
                text_lines = [line[1][0] for line in result[0] if line[1]]
                return '\n'.join(text_lines)
            return ""
        finally:
            os.unlink(tmp_path)

    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX document"""
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            doc = Document(tmp_path)
            text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
            return '\n\n'.join(text_parts)
        finally:
            os.unlink(tmp_path)

    def extract_and_upload_text(self, file_path: str) -> str:
        """
        Extract text from file and upload to MinIO

        Args:
            file_path: Source file path in MinIO

        Returns:
            MinIO path to extracted text file
        """
        # Extract text
        text = self.extract_text_from_file(file_path)

        # Upload text to MinIO
        filename = file_path.split("/")[-1].rsplit('.', 1)[0] + '.txt'
        text_path = self.minio.upload_file(
            content=text.encode('utf-8'),
            filename=filename,
            bucket_type="text"
        )

        return text_path
