from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InputType(str, Enum):
    VOICE = "voice"
    TEXT = "text"
    TOUCH = "touch"
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"


class ResponseBase(BaseModel):
    question_id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., description="Text of the question asked")
    answer_text: str = Field(..., description="Patient's answer text")
    input_type: InputType = Field(..., description="Input method used by patient")
    language: str = Field(..., description="Language code of response")


class ResponseCreate(ResponseBase):
    pass


class PatientResponse(ResponseBase):
    response_id: str = Field(..., description="Application-level response identifier (e.g., RESP-000001)")
    session_id: str = Field(..., description="Session identifier associated with this response")
    timestamp: datetime = Field(..., description="Timestamp when response was recorded")

    class Config:
        json_schema_extra = {
            "example": {
                "response_id": "RESP-000001",
                "session_id": "SES-000001",
                "question_id": "Q-CHEST-001",
                "question_text": "What is your main problem today?",
                "answer_text": "Mujhe do din se chest mein pain hai.",
                "input_type": "voice",
                "language": "hi",
                "timestamp": "2026-08-29T09:50:00Z"
            }
        }
