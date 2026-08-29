from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from .history import SourceType


class TimelineEventType(str, Enum):
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    INVESTIGATION = "investigation"
    PROCEDURE = "procedure"
    HOSPITALIZATION = "hospitalization"
    SURGERY = "surgery"
    SYMPTOM = "symptom"
    OTHER = "other"


class TimelineEventBase(BaseModel):
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    event_type: TimelineEventType = Field(..., description="Type of clinical timeline event")
    title: str = Field(..., description="Event title (e.g. ECG, Hypertension)")
    description: Optional[str] = Field(None, description="Detailed description of the event")
    source_type: SourceType = Field(..., description="Source origin type")
    source_id: str = Field(..., description="Source document or response identifier")


class TimelineEventCreate(TimelineEventBase):
    patient_id: str = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class TimelineEvent(TimelineEventBase):
    event_id: str = Field(..., description="Application-level event identifier (e.g., EVT-000001)")
    patient_id: str = Field(..., description="Patient identifier")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    created_at: datetime = Field(..., description="Timestamp when event was created")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "EVT-000001",
                "patient_id": "PAT-000001",
                "session_id": "SES-000001",
                "event_date": "2026-06-15",
                "event_type": "investigation",
                "title": "ECG",
                "description": "ECG recorded in uploaded medical report.",
                "source_type": "document",
                "source_id": "DOC-000004",
                "created_at": "2026-08-29T10:15:00Z"
            }
        }
