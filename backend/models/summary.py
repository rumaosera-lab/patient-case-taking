from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SummaryReviewStatus(str, Enum):
    GENERATED = "GENERATED"
    EDITED = "EDITED"
    APPROVED = "APPROVED"


class StructuredSummary(BaseModel):
    chief_complaint: Optional[str] = Field(None, description="Chief complaint summary")
    history_of_present_illness: Optional[str] = Field(None, description="HPI narrative summary")
    relevant_history: List[str] = Field(default_factory=list, description="Relevant past medical history")
    current_medications: List[str] = Field(default_factory=list, description="List of current medications")
    relevant_investigations: List[str] = Field(default_factory=list, description="Key investigation findings")
    allergies: Optional[str] = Field(None, description="Allergies status")


class CaseSummaryBase(BaseModel):
    summary_text: str = Field(..., description="Full text case summary for doctor")
    structured_summary: StructuredSummary = Field(..., description="Categorized structured summary fields")


class CaseSummaryCreate(CaseSummaryBase):
    patient_id: str = Field(..., description="Patient identifier")
    session_id: str = Field(..., description="Session identifier")


class CaseSummaryUpdate(BaseModel):
    summary_text: Optional[str] = None
    structured_summary: Optional[StructuredSummary] = None
    review_status: Optional[SummaryReviewStatus] = None
    doctor_notes: Optional[str] = None


class CaseSummary(CaseSummaryBase):
    summary_id: str = Field(..., description="Application-level summary identifier (e.g., SUM-000001)")
    patient_id: str = Field(..., description="Patient identifier")
    session_id: str = Field(..., description="Session identifier")
    generated_at: datetime = Field(..., description="Timestamp when summary was generated")
    reviewed_by: Optional[str] = Field(None, description="Doctor ID who reviewed the summary")
    review_status: SummaryReviewStatus = Field(
        default=SummaryReviewStatus.GENERATED,
        description="Review/approval status"
    )
    doctor_notes: Optional[str] = Field(None, description="Optional doctor notes")
    approved_at: Optional[datetime] = Field(None, description="Timestamp when approved")

    class Config:
        json_schema_extra = {
            "example": {
                "summary_id": "SUM-000001",
                "patient_id": "PAT-000001",
                "session_id": "SES-000001",
                "summary_text": "Patient reports intermittent central chest pain for 2 days.",
                "structured_summary": {
                    "chief_complaint": "Chest pain - 2 days",
                    "history_of_present_illness": "Central intermittent chest pain.",
                    "relevant_history": [
                        "Hypertension",
                        "Diabetes"
                    ],
                    "current_medications": [
                        "Amlodipine 5 mg"
                    ],
                    "relevant_investigations": [
                        "ECG - 2026-06-15"
                    ],
                    "allergies": "No allergy reported"
                },
                "generated_at": "2026-08-29T10:20:00Z",
                "reviewed_by": None,
                "review_status": "GENERATED",
                "doctor_notes": None,
                "approved_at": None
            }
        }
