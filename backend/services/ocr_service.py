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
    Service interface/stub for OCR / Vision document processing.
    Follows Section 28 of docs/API_CONTRACTS.md.
    """
    # Clean stub: returns structured output preserving document ID without fabricated facts
    return OCROutput(
        document_id=document_id,
        extracted_text=None,
        pages=[]
    )
