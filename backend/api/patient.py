from datetime import datetime, timezone
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.patient import PatientCreate, PatientUpdate, Patient
from backend.models.session import SessionStatus
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_patient_id

router = APIRouter()


@router.post("/patients", status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate):
    """
    Creates a new patient record in the database.
    """
    try:
        db = get_db()
        max_retries = 3
        patient_data = payload.model_dump()
        
        now = datetime.now(timezone.utc).isoformat()
        patient_data["created_at"] = now
        patient_data["updated_at"] = now

        for _ in range(max_retries):
            patient_id = generate_patient_id(db)
            patient_data["patient_id"] = patient_id
            
            try:
                db["patients"].insert_one(patient_data.copy())
                # Return standard success response matching API_CONTRACTS.md Section 10.1
                response_data = {
                    "patient_id": patient_id,
                    "name": patient_data["name"],
                    "preferred_language": patient_data["preferred_language"],
                    "date_of_birth": patient_data["date_of_birth"],
                    "gender": patient_data["gender"],
                    "phone": patient_data["phone"],
                    "abha_id": patient_data.get("abha_id")
                }
                return success_response(
                    data=response_data,
                    message="Patient registered successfully",
                    status_code=status.HTTP_201_CREATED
                )
            except DuplicateKeyError:
                continue

        return error_response(
            code="DUPLICATE_RESOURCE",
            message="Failed to generate unique patient ID due to high concurrency. Please try again.",
            status_code=status.HTTP_409_CONFLICT
        )

    except PyMongoError as e:
        return error_response(
            code="DATABASE_ERROR",
            message=f"Database operation failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return error_response(
            code="INTERNAL_SERVER_ERROR",
            message=f"An unexpected error occurred: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    """
    Retrieves a single patient record by application-level patient_id.
    """
    try:
        db = get_db()
        patient = db["patients"].find_one({"patient_id": patient_id}, {"_id": 0})
        
        if not patient:
            return error_response(
                code="PATIENT_NOT_FOUND",
                message=f"Patient with ID '{patient_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return success_response(data=patient)

    except PyMongoError as e:
        return error_response(
            code="DATABASE_ERROR",
            message=f"Database operation failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return error_response(
            code="INTERNAL_SERVER_ERROR",
            message=f"An unexpected error occurred: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.patch("/patients/{patient_id}")
def update_patient(patient_id: str, payload: PatientUpdate):
    """
    Partially updates an existing patient record.
    """
    try:
        db = get_db()
        existing = db["patients"].find_one({"patient_id": patient_id})
        if not existing:
            return error_response(
                code="PATIENT_NOT_FOUND",
                message=f"Patient with ID '{patient_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        update_data = payload.model_dump(exclude_unset=True)
        if update_data:
            now = datetime.now(timezone.utc).isoformat()
            update_data["updated_at"] = now
            db["patients"].update_one(
                {"patient_id": patient_id},
                {"$set": update_data}
            )

        updated_patient = db["patients"].find_one({"patient_id": patient_id}, {"_id": 0})
        return success_response(
            data=updated_patient,
            message="Patient updated successfully"
        )

    except PyMongoError as e:
        return error_response(
            code="DATABASE_ERROR",
            message=f"Database operation failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return error_response(
            code="INTERNAL_SERVER_ERROR",
            message=f"An unexpected error occurred: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/patients/{patient_id}/sessions/active")
def get_active_session(patient_id: str):
    """
    Retrieves the active (IN_PROGRESS) session for a patient, if one exists.
    """
    try:
        db = get_db()
        # Verify patient exists
        patient = db["patients"].find_one({"patient_id": patient_id})
        if not patient:
            return error_response(
                code="PATIENT_NOT_FOUND",
                message=f"Patient with ID '{patient_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        active_session = db["sessions"].find_one(
            {
                "patient_id": patient_id,
                "status": SessionStatus.IN_PROGRESS.value
            },
            {"_id": 0},
            sort=[("last_updated_at", -1), ("started_at", -1)]
        )

        if not active_session:
            return success_response(
                data=None,
                message="No active session found"
            )

        response_data = {
            "session_id": active_session["session_id"],
            "status": active_session["status"],
            "last_updated_at": active_session.get("last_updated_at", active_session.get("started_at"))
        }
        return success_response(data=response_data)

    except PyMongoError as e:
        return error_response(
            code="DATABASE_ERROR",
            message=f"Database operation failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return error_response(
            code="INTERNAL_SERVER_ERROR",
            message=f"An unexpected error occurred: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

