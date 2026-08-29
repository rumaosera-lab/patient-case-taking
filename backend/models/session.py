from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    READY_FOR_DOCTOR = "READY_FOR_DOCTOR"
    REVIEWED = "REVIEWED"


class SessionBase(BaseModel):
    patient_id: str = Field(..., description="Application-level patient identifier")
    department: str = Field(..., description="Medical department for the session")


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    department: Optional[str] = None
    completed_at: Optional[datetime] = None


class Session(SessionBase):
    session_id: str = Field(..., description="Application-level session identifier (e.g., SES-000001)")
    status: SessionStatus = Field(default=SessionStatus.IN_PROGRESS, description="Current session lifecycle status")
    started_at: datetime = Field(..., description="Timestamp when session started")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when session completed")
    last_updated_at: Optional[datetime] = Field(None, description="Timestamp when session was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "SES-000001",
                "patient_id": "PAT-000001",
                "status": "IN_PROGRESS",
                "department": "General Medicine",
                "started_at": "2026-08-29T09:30:00Z",
                "completed_at": None,
                "last_updated_at": "2026-08-29T09:45:00Z"
            }
        }
