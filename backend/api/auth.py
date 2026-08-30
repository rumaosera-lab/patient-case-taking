from typing import Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr, Field

from backend.database.connection import get_db
from backend.utils.responses import success_response, error_response

router = APIRouter()


class PatientLoginRequest(BaseModel):
    phone: str = Field(..., description="Patient contact phone number")
    password: str = Field(..., description="Patient login password/credential")


class DoctorLoginRequest(BaseModel):
    email: str = Field(..., description="Doctor login email address")
    password: str = Field(..., description="Doctor account password")


@router.post("/auth/patient/login")
def patient_login(payload: PatientLoginRequest):
    """
    Patient authentication endpoint (contract reserved for Phase 10).
    Follows Section 12.1 of docs/API_CONTRACTS.md.
    """
    db = get_db()
    patient = db["patients"].find_one({"phone": payload.phone}, {"_id": 0})
    user_id = patient.get("patient_id", "PAT-000001") if patient else "PAT-000001"

    return success_response(data={
        "access_token": f"dev_patient_token_{user_id}",
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "role": "patient"
        }
    })


@router.post("/auth/doctor/login")
def doctor_login(payload: DoctorLoginRequest):
    """
    Doctor authentication endpoint (contract reserved for Phase 10).
    Follows Section 12.2 of docs/API_CONTRACTS.md.
    """
    db = get_db()
    doctor = db["doctors"].find_one({"email": payload.email}, {"_id": 0})
    user_id = doctor.get("doctor_id", "DOC-000001") if doctor else "DOC-000001"

    return success_response(data={
        "access_token": f"dev_doctor_token_{user_id}",
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "role": "doctor"
        }
    })
