from datetime import datetime, timezone
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.session import SessionCreate, SessionUpdate, SessionStatus
from backend.models.response import ResponseCreate
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_session_id, generate_response_id

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
        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            if hasattr(new_status, "value"):
                new_status = new_status.value
            update_data["status"] = new_status
            current_status = existing_session.get("status", SessionStatus.IN_PROGRESS.value)
            
            valid_transitions = {
                SessionStatus.IN_PROGRESS.value: {
                    SessionStatus.IN_PROGRESS.value,
                    SessionStatus.PROCESSING.value,
                    SessionStatus.COMPLETED.value,
                    SessionStatus.READY_FOR_DOCTOR.value,
                },
                SessionStatus.PROCESSING.value: {
                    SessionStatus.PROCESSING.value,
                    SessionStatus.COMPLETED.value,
                    SessionStatus.READY_FOR_DOCTOR.value,
                },
                SessionStatus.COMPLETED.value: {
                    SessionStatus.COMPLETED.value,
                    SessionStatus.READY_FOR_DOCTOR.value,
                },
                SessionStatus.READY_FOR_DOCTOR.value: {
                    SessionStatus.READY_FOR_DOCTOR.value,
                    SessionStatus.REVIEWED.value,
                },
                SessionStatus.REVIEWED.value: {
                    SessionStatus.REVIEWED.value,
                },
            }

            allowed = valid_transitions.get(current_status, set())
            if new_status not in allowed:
                return error_response(
                    code="INVALID_REQUEST",
                    message=f"Invalid status transition from '{current_status}' to '{new_status}'",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

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


@router.post("/sessions/{session_id}/responses", status_code=status.HTTP_201_CREATED)
def submit_response(session_id: str, payload: ResponseCreate):
    """
    Submits a patient intake response associated with an active session.
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

        # Validate session status is IN_PROGRESS
        if session_doc.get("status") != SessionStatus.IN_PROGRESS.value:
            return error_response(
                code="INVALID_REQUEST",
                message=f"Cannot submit response to session with status '{session_doc.get('status')}'",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        now = datetime.now(timezone.utc).isoformat()
        resp_dict = payload.model_dump()
        if hasattr(resp_dict.get("input_type"), "value"):
            resp_dict["input_type"] = resp_dict["input_type"].value

        resp_dict["session_id"] = session_id
        resp_dict["timestamp"] = now

        max_retries = 3
        for _ in range(max_retries):
            response_id = generate_response_id(db)
            resp_dict["response_id"] = response_id

            try:
                db["responses"].insert_one(resp_dict.copy())
                # Update session last_updated_at
                db["sessions"].update_one(
                    {"session_id": session_id},
                    {"$set": {"last_updated_at": now}}
                )

                response_data = {
                    "response_id": response_id,
                    "session_id": session_id,
                    "question_id": resp_dict["question_id"],
                    "answer_text": resp_dict["answer_text"],
                    "input_type": resp_dict["input_type"],
                    "language": resp_dict["language"],
                    "timestamp": now
                }
                return success_response(
                    data=response_data,
                    status_code=status.HTTP_201_CREATED
                )
            except DuplicateKeyError:
                continue

        return error_response(
            code="DUPLICATE_RESOURCE",
            message="Failed to generate unique response ID due to high concurrency. Please try again.",
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


@router.get("/sessions/{session_id}/responses")
def get_responses(session_id: str):
    """
    Retrieves all recorded responses for a session in chronological order.
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

        responses = list(db["responses"].find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1))

        return success_response(data=responses)

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

