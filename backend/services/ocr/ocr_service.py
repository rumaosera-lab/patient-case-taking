"""
ocr_service.py
---------------
Responsibility:
    Document (PDF / image) -> raw extracted text

Pipeline position:
    Uploaded file -> [ocr_service] -> raw extracted text -> document_processor.py

Design notes:
    - Primary OCR/vision: Gemini Vision / document understanding.
    - Fallback OCR: PaddleOCR (used if Gemini is unavailable or fails on supported image types).
    - This module does NOT attempt any medical interpretation or diagnosis.
      It only transcribes pixels/PDF content faithfully into text.
    - Preserves the established OCR output contract from docs/API_CONTRACTS.md Section 28.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv

# Load backend/.env safely across different execution environments
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()  # Fallback to current working directory .env if present

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini vision/document model (defaults to gemini-3.6-flash)
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Prompt strictly enforces faithful transcription without medical inference or hallucination
OCR_PROMPT = (
    "You are an OCR engine. Extract ALL text visible in this medical "
    "document exactly as it is written, including headers, dates, "
    "drug names, dosages, and any handwritten notes if legible.\n"
    "Rules:\n"
    "- Do not summarize, interpret, or correct anything.\n"
    "- Do not add information that is not visibly present.\n"
    "- Preserve the original line structure as closely as possible.\n"
    "- If a word is illegible, write [illegible] instead of guessing.\n"
    "Return plain text only, no explanations, no markdown."
)


@dataclass
class OCRPageResult:
    """Raw OCR output for a single page of a document."""
    page_number: int
    text: str
    confidence: Optional[float] = None
    engine_used: Optional[str] = None  # "gemini_vision" | "paddleocr"


@dataclass
class OCRResult:
    """Raw OCR output for an entire document."""
    document_id: str
    filename: str
    pages: List[OCRPageResult] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """All pages concatenated in chronological/sequential order."""
        return "\n\n".join(p.text for p in self.pages if p.text)

    def to_contract_dict(self) -> Dict[str, Any]:
        """
        Matches the OCR Output contract exactly (docs/API_CONTRACTS.md Section 28):
        {
            "document_id": "DOC-000001",
            "extracted_text": "...",
            "pages": [
                {"page": 1, "text": "..."}
            ]
        }
        """
        return {
            "document_id": self.document_id,
            "extracted_text": self.full_text,
            "pages": [{"page": p.page_number, "text": p.text} for p in self.pages],
        }


def extract_text_from_file(
    document_id: str,
    filename: str,
    file_bytes: bytes,
    content_type: str,
) -> OCRResult:
    """
    Main entry point: turn uploaded document bytes into raw transcribed text.

    Args:
        document_id: Application document ID (e.g., DOC-000001).
        filename: Original file name (e.g., "prescription.pdf").
        file_bytes: Raw binary content of the file.
        content_type: MIME type (e.g., "application/pdf", "image/jpeg", "image/png").

    Returns:
        OCRResult containing per-page raw text and full_text property.
    """
    if not file_bytes:
        raise ValueError("Cannot extract text from empty or missing file bytes")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Ensure GEMINI_API_KEY is configured in backend/.env."
        )

    engine = "gemini_vision"
    try:
        text = _extract_with_gemini(file_bytes, content_type)
    except Exception as gemini_error:
        # Fallback to local OCR if Gemini call fails and input is an image
        try:
            text = _extract_with_paddleocr(file_bytes, content_type)
            engine = "paddleocr"
        except (NotImplementedError, ImportError, Exception):
            # If fallback is unavailable or unsupported for this format, raise the primary Gemini error
            raise gemini_error

    page = OCRPageResult(page_number=1, text=text, engine_used=engine)
    return OCRResult(document_id=document_id, filename=filename, pages=[page])


def _extract_with_gemini(file_bytes: bytes, content_type: str) -> str:
    """
    Calls Gemini document understanding to extract raw text from image or PDF bytes.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Ensure GEMINI_API_KEY is configured in backend/.env."
        )

    model_name = os.getenv("GEMINI_MODEL", GEMINI_MODEL_NAME)
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=[
                genai.types.Part.from_bytes(data=file_bytes, mime_type=content_type),
                OCR_PROMPT
            ]
        )
        if not response or not response.text:
            raise ValueError("Gemini returned an empty response for this document")
        return response.text.strip()
    except Exception:
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(model_name)
            response = model.generate_content([
                OCR_PROMPT,
                {"mime_type": content_type, "data": file_bytes},
            ])
            if not response or not response.text:
                raise ValueError("Gemini returned an empty response for this document")
            return response.text.strip()
        except Exception as err:
            raise err


_paddle_ocr_instance = None


def _extract_with_paddleocr(file_bytes: bytes, content_type: str) -> str:
    """
    Fallback OCR using PaddleOCR when Gemini Vision is unavailable.
    Applies only to image formats.
    """
    if "pdf" in content_type.lower():
        raise NotImplementedError(
            "PaddleOCR fallback does not support direct PDF files, only images."
        )

    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr_instance = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except ImportError as e:
            raise NotImplementedError("PaddleOCR is not installed in the current environment.") from e

    import io
    import numpy as np
    from PIL import Image

    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image_np = np.array(image)

    result = _paddle_ocr_instance.ocr(image_np, cls=True)

    lines = []
    if result:
        for page_result in result:
            if not page_result:
                continue
            for detection in page_result:
                text = detection[1][0]
                lines.append(text)

    if not lines:
        raise ValueError("PaddleOCR found no readable text in this image")

    return "\n".join(lines)