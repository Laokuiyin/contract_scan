"""AI extraction service using Qwen API"""

import json
from typing import Dict, Any, Optional
import httpx
from app.services.minio_service import MinIOService
from app.core.config import settings


class AIExtractionService:
    """Service for AI-powered contract field extraction"""

    def __init__(self):
        """Initialize AI extraction service"""
        self.minio = MinIOService()
        self.api_key = settings.qwen_api_key
        self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.model_version = "qwen-plus"

    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for contract field extraction"""
        return f"""请从以下合同文本中提取关键信息，以JSON格式返回：

合同文本：
{text}

请提取以下字段（如果找不到则返回null）：
{{
  "total_amount": 合同总金额（数字），
  "subject_matter": 合同标的物，
  "sign_date": 签订日期（ISO格式），
  "effective_date": 生效日期（ISO格式），
  "expire_date": 截止日期（ISO格式），
  "parties": [
    {{
      "party_type": "甲方"或"乙方"，
      "party_name": 单位名称，
      "tax_number": 税号（如果有），
      "legal_representative": 法定代表人（如果有），
      "address": 地址（如果有）
    }}
  ]
}}

请只返回JSON，不要包含其他说明文字。"""

    async def extract_fields(self, text_content: str) -> Dict[str, Any]:
        """
        Extract contract fields using AI

        Args:
            text_content: Contract text content

        Returns:
            Dict with extracted fields and confidence scores
        """
        # Build prompt
        prompt = self._build_extraction_prompt(text_content)

        # Call Qwen API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_version,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Low temperature for consistent extraction
            "max_tokens": 2000
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

        # Parse response
        ai_message = result["choices"][0]["message"]["content"]

        # Extract JSON from response
        try:
            # Try to parse directly
            if ai_message.strip().startswith("{"):
                extracted = json.loads(ai_message)
            else:
                # Extract JSON from markdown code block
                start = ai_message.find("{")
                end = ai_message.rfind("}") + 1
                extracted = json.loads(ai_message[start:end])
        except json.JSONDecodeError:
            extracted = {
                "total_amount": None,
                "subject_matter": None,
                "sign_date": None,
                "effective_date": None,
                "expire_date": None,
                "parties": []
            }

        # Calculate confidence score (simplified)
        confidence = self._calculate_confidence(extracted, text_content)

        return {
            "extracted_data": extracted,
            "confidence_score": confidence,
            "model_version": self.model_version
        }

    def _calculate_confidence(self, extracted: Dict, text: str) -> float:
        """Calculate confidence score based on extraction completeness"""
        fields = ["total_amount", "subject_matter", "sign_date", "effective_date", "expire_date"]
        found = sum(1 for field in fields if extracted.get(field) not in [None, ""])

        # Bonus for parties
        parties = extracted.get("parties", [])
        if parties:
            found += min(len(parties), 2) * 0.5

        confidence = (found / len(fields)) * 0.9 + 0.1  # Min 0.1
        return round(confidence, 2)

    async def extract_from_minio_file(self, text_file_path: str) -> Dict[str, Any]:
        """
        Extract fields from text file in MinIO

        Args:
            text_file_path: MinIO path to text file

        Returns:
            Dict with extracted fields
        """
        # Get text content from MinIO
        text_content_bytes = self.minio.get_file(text_file_path)
        text_content = text_content_bytes.decode('utf-8')

        # Extract fields
        return await self.extract_fields(text_content)
