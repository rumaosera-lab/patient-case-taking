from datetime import datetime, timezone
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.history import ClinicalHistoryUpdate
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_history_id

router = APIRouter()


@router.get("/sessions/{session_id}/history")
def get_clinical_history(session_id: str):
    """
    Retrieves structured clinical history for a session.
    Matching docs/API_CONTRACTS.md Section 15.2.
    """
    try:
        db = get_db()
        
        # Verify session exists
        session_doc = db["sessions"].find_one({"session_id": session_id})
        if not session_doc:
            return error_response(
                code="SESSION_NOT_FOUND",
                message=f"Session with ID '{session_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        history_doc = db["clinical_histories"].find_one({"session_id": session_id}, {"_id": 0})
        
        if not history_doc:
            # Return empty structured history envelope if not initialized yet
            now = datetime.now(timezone.utc).isoformat()
            empty_history = {
                "history_id": None,
                "session_id": session_id,
                "chief_complaint": None,
                "history_of_present_illness": None,
                "past_medical_history": [],
                "past_surgical_history": [],
                "current_medications": [],
                "allergies": [],
                "family_history": [],
                "personal_history": [],
                "review_of_systems": [],
                "created_at": None,
                "updated_at": None
            }
            return success_response(data=empty_history)

        return success_response(data=history_doc)

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


@router.patch("/sessions/{session_id}/history")
def update_clinical_history(session_id: str, payload: ClinicalHistoryUpdate):
    """
    Partially updates structured clinical history for a session.
    Matching docs/API_CONTRACTS.md Section 15.3.
    """
    try:
        db = get_db()
        
        # Verify session exists
        session_doc = db["sessions"].find_one({"session_id": session_id})
        if not session_doc:
            return error_response(
                code="SESSION_NOT_FOUND",
                message=f"Session with ID '{session_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        now = datetime.now(timezone.utc).isoformat()
        update_fields = payload.model_dump(exclude_unset=True)
        update_fields["updated_at"] = now

        existing_history = db["clinical_histories"].find_one({"session_id": session_id})
        
        if existing_history:
            db["clinical_histories"].update_one(
                {"session_id": session_id},
                {"$set": update_fields}
            )
        else:
            # Initialize new history record
            history_id = generate_history_id(db)
            new_history = {
                "history_id": history_id,
                "session_id": session_id,
                "chief_complaint": update_fields.get("chief_complaint"),
                "history_of_present_illness": update_fields.get("history_of_present_illness"),
                "past_medical_history": update_fields.get("past_medical_history", []),
                "past_surgical_history": update_fields.get("past_surgical_history", []),
                "current_medications": update_fields.get("current_medications", []),
                "allergies": update_fields.get("allergies", []),
                "family_history": update_fields.get("family_history", []),
                "personal_history": update_fields.get("personal_history", []),
                "review_of_systems": update_fields.get("review_of_systems", []),
                "created_at": now,
                "updated_at": now
            }
            db["clinical_histories"].insert_one(new_history)

        updated_history = db["clinical_histories"].find_one({"session_id": session_id}, {"_id": 0})
        return success_response(
            data=updated_history,
            message="Clinical history updated successfully"
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
