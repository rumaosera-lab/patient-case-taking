from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    MEDICAL_REPORT = "medical_report"
    OTHER = "other"


class DocumentProcessingStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class DocumentBase(BaseModel):
    file_name: str = Field(..., description="Original file name")
    document_type: DocumentType = Field(..., description="Category of medical document")


class DocumentCreate(DocumentBase):
    patient_id: str = Field(..., description="Patient ID")
    session_id: str = Field(..., description="Session ID")


class Document(DocumentBase):
    document_id: str = Field(..., description="Application-level document identifier (e.g., DOC-000001)")
    patient_id: str = Field(..., description="Patient ID associated with this document")
    session_id: str = Field(..., description="Session ID associated with this document")
    file_url: Optional[str] = Field(None, description="Storage URL or file path")
    processing_status: DocumentProcessingStatus = Field(
        default=DocumentProcessingStatus.UPLOADED,
        description="Current OCR/processing pipeline status"
    )
    uploaded_at: datetime = Field(..., description="Timestamp when file was uploaded")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "DOC-000001",
                "patient_id": "PAT-000001",
                "session_id": "SES-000001",
                "file_name": "prescription.pdf",
                "document_type": "prescription",
                "file_url": None,
                "processing_status": "UPLOADED",
                "uploaded_at": "2026-08-29T10:05:00Z"
            }
        }
