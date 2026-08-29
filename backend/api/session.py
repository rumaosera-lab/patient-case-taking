from datetime import datetime, timezone
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.session import SessionCreate, SessionUpdate, SessionStatus
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_session_id

router = APIRouter()


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate):
    """
    Creates a new patient session/visit after verifying patient existence.
    """
    try:
        db = get_db()
        
        # Verify patient exists
        patient = db["patients"].find_one({"patient_id": payload.patient_id})
        if not patient:
            return error_response(
                code="PATIENT_NOT_FOUND",
                message=f"Patient with ID '{payload.patient_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        now = datetime.now(timezone.utc).isoformat()
        session_data = payload.model_dump()
        session_data["status"] = SessionStatus.IN_PROGRESS.value
        session_data["started_at"] = now
        session_data["completed_at"] = None
        session_data["last_updated_at"] = now

        max_retries = 3
        for _ in range(max_retries):
            session_id = generate_session_id(db)
            session_data["session_id"] = session_id
            
            try:
                db["sessions"].insert_one(session_data.copy())
                response_data = {
                    "session_id": session_id,
                    "patient_id": session_data["patient_id"],
                    "status": session_data["status"],
                    "department": session_data["department"],
                    "started_at": session_data["started_at"]
                }
                return success_response(
                    data=response_data,
                    status_code=status.HTTP_201_CREATED
                )
            except DuplicateKeyError:
                continue

        return error_response(
            code="DUPLICATE_RESOURCE",
            message="Failed to generate unique session ID due to high concurrency. Please try again.",
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


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """
    Retrieves a single session record by application-level session_id.
    """
    try:
        db = get_db()
        session_doc = db["sessions"].find_one({"session_id": session_id}, {"_id": 0})
        
        if not session_doc:
            return error_response(
                code="SESSION_NOT_FOUND",
                message=f"Session with ID '{session_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return success_response(data=session_doc)

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


@router.patch("/sessions/{session_id}")
def update_session(session_id: str, payload: SessionUpdate):
    """
    Partially updates an existing session (status, department, completed_at).
    Automatically refreshes last_updated_at timestamp.
    """
    try:
        db = get_db()
        
        # Verify session exists
        existing_session = db["sessions"].find_one({"session_id": session_id})
        if not existing_session:
            return error_response(
                code="SESSION_NOT_FOUND",
                message=f"Session with ID '{session_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        update_data = payload.model_dump(exclude_unset=True)
        if "completed_at" in update_data and isinstance(update_data["completed_at"], datetime):
            update_data["completed_at"] = update_data["completed_at"].isoformat()

        # Always update last_updated_at on backend
        now = datetime.now(timezone.utc).isoformat()
        update_data["last_updated_at"] = now

        db["sessions"].update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )

        updated_session = db["sessions"].find_one({"session_id": session_id}, {"_id": 0})
        return success_response(
            data=updated_session,
            message="Session updated successfully"
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
