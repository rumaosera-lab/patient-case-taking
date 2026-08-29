from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractedInformationBase(BaseModel):
    diagnoses: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted diagnoses")
    medications: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted medications with dosage/frequency")
    investigations: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted lab/investigation results")
    procedures: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted medical procedures")
    extracted_text: Optional[str] = Field(None, description="Raw OCR extracted text")
    confidence: Optional[float] = Field(None, description="Extraction confidence score (0.0 to 1.0)")


class ExtractedInformationCreate(ExtractedInformationBase):
    document_id: str = Field(..., description="Source document identifier")
    patient_id: str = Field(..., description="Patient identifier")


class ExtractedInformation(ExtractedInformationBase):
    extraction_id: str = Field(..., description="Application-level extraction identifier (e.g., EXT-000001)")
    document_id: str = Field(..., description="Source document identifier")
    patient_id: str = Field(..., description="Patient identifier")
    created_at: datetime = Field(..., description="Timestamp when extraction occurred")

    class Config:
        json_schema_extra = {
            "example": {
                "extraction_id": "EXT-000001",
                "document_id": "DOC-000001",
                "patient_id": "PAT-000001",
                "diagnoses": [],
                "medications": [
                    {
                        "medicine": "Amlodipine",
                        "dosage": "5 mg",
                        "frequency": "once daily",
                        "source": {
                            "type": "document",
                            "source_id": "DOC-000001",
                            "page": 1
                        }
                    }
                ],
                "investigations": [],
                "procedures": [],
                "extracted_text": "Tab Amlodipine 5 mg once daily...",
                "confidence": 0.94,
                "created_at": "2026-08-29T10:10:00Z"
            }
        }
