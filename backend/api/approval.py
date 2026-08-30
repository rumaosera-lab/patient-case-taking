from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from backend.database.connection import get_db
from backend.models.session import SessionStatus
from backend.models.summary import SummaryReviewStatus
from backend.utils.responses import success_response, error_response

router = APIRouter()


class ApprovalRequest(BaseModel):
    reviewed_by: Optional[str] = Field(default="DOC-000001", description="Doctor identifier approving the record")
    doctor_notes: Optional[str] = Field(None, description="Optional notes from approving doctor")


@router.post("/sessions/{session_id}/approve")
def approve_session(session_id: str, payload: Optional[ApprovalRequest] = None):
    """
    Approves and finalizes a patient case record.
    Follows Section 23 of docs/API_CONTRACTS.md.
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

        current_status = session_doc.get("status")
        if current_status == SessionStatus.REVIEWED.value:
            return error_response(
                code="INVALID_REQUEST",
                message=f"Session '{session_id}' is already approved and reviewed.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        now = datetime.now(timezone.utc).isoformat()
        doctor_id = (payload.reviewed_by if payload and payload.reviewed_by else "DOC-000001")
        notes = (payload.doctor_notes if payload else None)

        # Update session status
        db["sessions"].update_one(
            {"session_id": session_id},
            {"$set": {
                "status": SessionStatus.REVIEWED.value,
                "last_updated_at": now
            }}
        )

        # Update case summary if exists, or create approved summary record
        existing_summary = db["case_summaries"].find_one({"session_id": session_id})
        if existing_summary:
            summary_update = {
                "review_status": SummaryReviewStatus.APPROVED.value,
                "reviewed_by": doctor_id,
                "approved_at": now
            }
            if notes:
                summary_update["doctor_notes"] = notes
            db["case_summaries"].update_one(
                {"session_id": session_id},
                {"$set": summary_update}
            )

        response_data = {
            "session_id": session_id,
            "status": SessionStatus.REVIEWED.value,
            "review_status": SummaryReviewStatus.APPROVED.value,
            "reviewed_by": doctor_id,
            "approved_at": now
        }

        return success_response(
            data=response_data,
            message="Patient record approved successfully"
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
