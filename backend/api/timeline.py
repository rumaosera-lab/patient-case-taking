from fastapi import APIRouter, status
from pymongo.errors import PyMongoError

from backend.database.connection import get_db
from backend.utils.responses import success_response, error_response

router = APIRouter()


@router.get("/patients/{patient_id}/timeline")
def get_patient_timeline(patient_id: str):
    """
    Retrieves chronological medical timeline events for a patient.
    Follows Section 19 of docs/API_CONTRACTS.md.
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

        events = list(db["timeline_events"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort([("event_date", 1), ("created_at", 1)]))

        return success_response(data={
            "patient_id": patient_id,
            "events": events
        })

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
