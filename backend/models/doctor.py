from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class DoctorBase(BaseModel):
    name: str = Field(..., description="Doctor's full name")
    email: str = Field(..., description="Doctor's email address")
    department: str = Field(..., description="Medical department")


class DoctorCreate(DoctorBase):
    password: str = Field(..., description="Account password")


class DoctorInDB(DoctorBase):
    doctor_id: str = Field(..., description="Application-level doctor identifier (e.g., DOC-000001)")
    password_hash: str = Field(..., description="Hashed password for database storage")
    created_at: Optional[datetime] = Field(None, description="Timestamp when record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when record was last updated")


class Doctor(DoctorBase):
    doctor_id: str = Field(..., description="Application-level doctor identifier (e.g., DOC-000001)")
    created_at: Optional[datetime] = Field(None, description="Timestamp when record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when record was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "doctor_id": "DOC-000001",
                "name": "Dr. Mehta",
                "email": "doctor@example.com",
                "department": "General Medicine",
                "created_at": "2026-08-29T09:00:00Z",
                "updated_at": "2026-08-29T09:00:00Z"
            }
        }
