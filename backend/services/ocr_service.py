import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OCRPage(BaseModel):
    page: int = Field(..., description="Page index (1-indexed)")
    text: str = Field(..., description="Extracted text on page")


class OCROutput(BaseModel):
    document_id: str = Field(..., description="Application-level document identifier")
    extracted_text: Optional[str] = Field(None, description="Full combined extracted text")
    pages: List[OCRPage] = Field(default_factory=list, description="Extracted text per page")


def process_document_ocr(document_id: str, file_bytes: bytes, filename: str) -> OCROutput:
    """
    Service for OCR / Vision document processing.
    Follows Section 28 of docs/API_CONTRACTS.md.
    """
    if not file_bytes:
        return OCROutput(
            document_id=document_id,
            extracted_text=None,
            pages=[]
        )

    # Check for text in plain text or simple PDF
    text_content = ""
    try:
        # Try decoding as utf-8 or ascii if text file
        if filename.lower().endswith((".txt", ".csv")):
            text_content = file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # Optional Gemini Vision for OCR
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and not text_content:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            mime_type = "application/pdf" if filename.lower().endswith(".pdf") else "image/jpeg"
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    genai.types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    "Extract all text from this medical document accurately without altering numbers or medication names."
                ]
            )
            if response and response.text:
                text_content = response.text
        except Exception:
            pass

    if text_content and text_content.strip():
        pages = [OCRPage(page=1, text=text_content.strip())]
        return OCROutput(
            document_id=document_id,
            extracted_text=text_content.strip(),
            pages=pages
        )

    return OCROutput(
        document_id=document_id,
        extracted_text=None,
        pages=[]
    )
