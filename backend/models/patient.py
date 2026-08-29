from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PatientBase(BaseModel):
    name: str = Field(..., description="Full name of the patient")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    gender: str = Field(..., description="Gender of the patient (e.g., Male, Female, Other)")
    phone: str = Field(..., description="Contact phone number")
    preferred_language: str = Field(..., description="Preferred language code (e.g., en, hi, mr)")
    abha_id: Optional[str] = Field(None, description="Optional ABHA health ID")


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: Optional[str] = None
    abha_id: Optional[str] = None


class Patient(PatientBase):
    patient_id: str = Field(..., description="Application-level patient identifier (e.g., PAT-000001)")
    created_at: Optional[datetime] = Field(None, description="Timestamp when record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when record was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "PAT-000001",
                "name": "Rahul Sharma",
                "date_of_birth": "1981-04-12",
                "gender": "Male",
                "phone": "9876543210",
                "preferred_language": "hi",
                "abha_id": None
            }
        }
