from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.response import ResponseCreate
from backend.models.session import SessionStatus
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_response_id

router = APIRouter()


@router.post("/sessions/{session_id}/responses", status_code=status.HTTP_201_CREATED)
def submit_response(session_id: str, payload: ResponseCreate):
    """
    Submits a patient's response to a clinical question.
    Matching docs/API_CONTRACTS.md Section 14.3.
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
        response_data = payload.model_dump()
        if hasattr(response_data.get("input_type"), "value"):
            response_data["input_type"] = response_data["input_type"].value
        response_data["session_id"] = session_id
        response_data["timestamp"] = now

        max_retries = 3
        for _ in range(max_retries):
            resp_id = generate_response_id(db)
            response_data["response_id"] = resp_id

            try:
                db["responses"].insert_one(response_data.copy())
                # Update session last_updated_at
                db["sessions"].update_one(
                    {"session_id": session_id},
                    {"$set": {"last_updated_at": now}}
                )
                # Return standard success response envelope matching contract example
                response_payload = {
                    "response_id": resp_id,
                    "session_id": session_id,
                    "question_id": response_data["question_id"],
                    "answer_text": response_data["answer_text"],
                    "input_type": response_data["input_type"],
                    "language": response_data["language"],
                    "timestamp": now
                }
                return success_response(
                    data=response_payload,
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
    Retrieves all recorded patient responses for a session in chronological order.
    Matching docs/API_CONTRACTS.md Section 14.4.
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

        responses_cursor = db["responses"].find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1)

        responses_list = list(responses_cursor)
        return success_response(data=responses_list)

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
