from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PATIENT_RESPONSE = "patient_response"
    DOCUMENT = "document"
    PREVIOUS_RECORD = "previous_record"


class SourceRef(BaseModel):
    type: SourceType = Field(..., description="Source type of information")
    source_id: str = Field(..., description="ID of source entity")
    page: Optional[int] = Field(None, description="Page number if source is document")


class FieldWithSource(BaseModel):
    value: Any = Field(..., description="Extracted fact value")
    source: Optional[SourceRef] = Field(None, description="Traceability source metadata")


class ClinicalHistoryBase(BaseModel):
    chief_complaint: Optional[Dict[str, Any]] = Field(None, description="Chief complaint with source reference")
    history_of_present_illness: Optional[Dict[str, Any]] = Field(None, description="HPI structured fields with sources")
    past_medical_history: List[Dict[str, Any]] = Field(default_factory=list, description="Past medical history items")
    past_surgical_history: List[Dict[str, Any]] = Field(default_factory=list, description="Past surgical history items")
    current_medications: List[Dict[str, Any]] = Field(default_factory=list, description="Current medications")
    allergies: List[Dict[str, Any]] = Field(default_factory=list, description="Reported allergies")
    family_history: List[Dict[str, Any]] = Field(default_factory=list, description="Family medical history")
    personal_history: List[Dict[str, Any]] = Field(default_factory=list, description="Personal/lifestyle history")
    review_of_systems: List[Dict[str, Any]] = Field(default_factory=list, description="Review of systems items")


class ClinicalHistoryCreate(ClinicalHistoryBase):
    session_id: str = Field(..., description="Session identifier")


class ClinicalHistoryUpdate(BaseModel):
    chief_complaint: Optional[Dict[str, Any]] = None
    history_of_present_illness: Optional[Dict[str, Any]] = None
    past_medical_history: Optional[List[Dict[str, Any]]] = None
    past_surgical_history: Optional[List[Dict[str, Any]]] = None
    current_medications: Optional[List[Dict[str, Any]]] = None
    allergies: Optional[List[Dict[str, Any]]] = None
    family_history: Optional[List[Dict[str, Any]]] = None
    personal_history: Optional[List[Dict[str, Any]]] = None
    review_of_systems: Optional[List[Dict[str, Any]]] = None


class ClinicalHistory(ClinicalHistoryBase):
    history_id: str = Field(..., description="Application-level history identifier (e.g., HIS-000001)")
    session_id: str = Field(..., description="Session identifier")
    created_at: Optional[datetime] = Field(None, description="Timestamp when created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "history_id": "HIS-000001",
                "session_id": "SES-000001",
                "chief_complaint": {
                    "value": "chest pain",
                    "source": {
                        "type": "patient_response",
                        "source_id": "RESP-000001"
                    }
                },
                "history_of_present_illness": {
                    "duration": {
                        "value": "2 days",
                        "source": {
                            "type": "patient_response",
                            "source_id": "RESP-000001"
                        }
                    }
                },
                "past_medical_history": [],
                "past_surgical_history": [],
                "current_medications": [],
                "allergies": [],
                "family_history": [],
                "personal_history": [],
                "review_of_systems": [],
                "created_at": "2026-08-29T10:00:00Z",
                "updated_at": "2026-08-29T10:00:00Z"
            }
        }
