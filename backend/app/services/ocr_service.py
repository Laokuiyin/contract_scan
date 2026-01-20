"""OCR service using Baidu OCR"""

import io
import tempfile
import os
import base64
import requests
from typing import Optional
from pdfplumber import PDF
from docx import Document
from pathlib import Path
from app.core.config import settings


class BaiduOCRService:
    """Baidu OCR service for text extraction from images"""

    def __init__(self):
        self.api_key = settings.baidu_ocr_api_key
        self.secret_key = settings.baidu_ocr_secret_key
        self.access_token = None

    def get_access_token(self):
        """Get Baidu OCR access token"""
        if self.access_token:
            return self.access_token

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }

        response = requests.post(url, params=params)
        result = response.json()

        if "access_token" in result:
            self.access_token = result["access_token"]
            return self.access_token
        else:
            raise Exception(f"Failed to get access token: {result}")

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using Baidu OCR"""
        access_token = self.get_access_token()

        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode()

        # Baidu OCR API
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'image': base64_image}

        response = requests.post(url, headers=headers, data=data)
        result = response.json()

        if "words_result" in result:
            text_lines = [item["words"] for item in result["words_result"]]
            return '\n'.join(text_lines)
        else:
            raise Exception(f"Baidu OCR error: {result}")


class OCRService:
    """Service for OCR text extraction from PDF, images, and DOCX files"""

    def __init__(self):
        """Initialize OCR service - Baidu OCR only"""
        self.baidu_ocr = None
        try:
            self.baidu_ocr = BaiduOCRService()
            print("Baidu OCR initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize Baidu OCR: {e}")
            raise Exception("Baidu OCR is required but failed to initialize")

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text from a local file

        Args:
            file_path: Local file path

        Returns:
            Extracted text content
        """
        # Get file extension
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        # Extract text based on file type
        if ext == '.pdf':
            return self._extract_from_pdf(file_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            return self._extract_from_image(file_path)
        elif ext == '.docx':
            return self._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        text_parts = []

        try:
            with PDF.open(file_path) as pdf:
                for page in pdf.pages:
                    # Try to extract text directly first
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(text)
                    else:
                        # If no text, try OCR on page image
                        if self.baidu_ocr:
                            try:
                                img = page.to_image()
                                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                                    img.save(tmp)
                                    tmp_path = tmp.name
                                text = self.baidu_ocr.extract_text_from_image(tmp_path)
                                os.unlink(tmp_path)
                                if text:
                                    text_parts.append(text)
                            except Exception as e:
                                print(f"Baidu OCR error on PDF page: {e}")
        except Exception as e:
            print(f"PDF extraction error: {e}")

        return '\n\n'.join(text_parts)

    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from image using Baidu OCR"""
        if not self.baidu_ocr:
            raise Exception("Baidu OCR is not available")

        try:
            return self.baidu_ocr.extract_text_from_image(file_path)
        except Exception as e:
            print(f"Baidu OCR error: {e}")
            raise e

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX document"""
        try:
            doc = Document(file_path)
            text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
            return '\n\n'.join(text_parts)
        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""

    def extract_and_save_text(self, file_path: str) -> str:
        """
        Extract text from file and save to local text file

        Args:
            file_path: Source file path

        Returns:
            Local path to extracted text file
        """
        # Extract text
        text = self.extract_text_from_file(file_path)

        # Save text file
        text_filename = file_path.rsplit('.', 1)[0] + '.txt'
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(text)

        return text_filename
