from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.summary import CaseSummaryCreate, SummaryReviewStatus, StructuredSummary
from backend.services.ai_service import generate_case_summary_text
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_summary_id

router = APIRouter()


@router.post("/sessions/{session_id}/summary", status_code=status.HTTP_201_CREATED)
def generate_summary(session_id: str, payload: Optional[CaseSummaryCreate] = None):
    """
    Creates/generates a physician-facing case summary draft for a session.
    Matching docs/API_CONTRACTS.md Section 20.3.
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
        patient_id = session_doc["patient_id"]

        if payload:
            summary_data = payload.model_dump()
            summary_text = summary_data.get("summary_text")
            structured_summary = summary_data.get("structured_summary")
        else:
            patient_doc = db["patients"].find_one({"patient_id": patient_id}, {"_id": 0}) or {}
            history_doc = db["clinical_histories"].find_one({"session_id": session_id}, {"_id": 0})
            responses = list(db["responses"].find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1))
            ai_draft = generate_case_summary_text(patient_doc, history_doc, responses)
            summary_text = ai_draft["summary_text"]
            structured_summary = ai_draft["structured_summary"]

        existing_summary = db["case_summaries"].find_one({"session_id": session_id})
        if existing_summary:
            summary_id = existing_summary["summary_id"]
            db["case_summaries"].update_one(
                {"session_id": session_id},
                {"$set": {
                    "summary_text": summary_text,
                    "structured_summary": structured_summary,
                    "generated_at": now,
                    "review_status": SummaryReviewStatus.GENERATED.value,
                    "reviewed_by": None,
                    "doctor_notes": None,
                    "approved_at": None
                }}
            )
            saved_summary = db["case_summaries"].find_one({"session_id": session_id}, {"_id": 0})
            return success_response(
                data=saved_summary,
                message="Case summary generated successfully",
                status_code=status.HTTP_201_CREATED
            )
        else:
            max_retries = 3
            for _ in range(max_retries):
                summary_id = generate_summary_id(db)
                summary_record = {
                    "summary_id": summary_id,
                    "patient_id": patient_id,
                    "session_id": session_id,
                    "summary_text": summary_text,
                    "structured_summary": structured_summary,
                    "generated_at": now,
                    "reviewed_by": None,
                    "review_status": SummaryReviewStatus.GENERATED.value,
                    "doctor_notes": None,
                    "approved_at": None
                }

                try:
                    db["case_summaries"].insert_one(summary_record.copy())
                    saved_summary = db["case_summaries"].find_one({"session_id": session_id}, {"_id": 0})
                    # Refresh session last_updated_at
                    db["sessions"].update_one(
                        {"session_id": session_id},
                        {"$set": {"last_updated_at": now}}
                    )
                    return success_response(
                        data=saved_summary,
                        message="Case summary generated successfully",
                        status_code=status.HTTP_201_CREATED
                    )
                except DuplicateKeyError:
                    continue

        return error_response(
            code="DUPLICATE_RESOURCE",
            message="Failed to generate unique summary ID due to high concurrency. Please try again.",
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


@router.get("/sessions/{session_id}/summary")
def get_summary(session_id: str):
    """
    Retrieves the case summary for a session.
    Matching docs/API_CONTRACTS.md Section 20.4.
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

        summary_doc = db["case_summaries"].find_one({"session_id": session_id}, {"_id": 0})
        if not summary_doc:
            return error_response(
                code="SUMMARY_NOT_FOUND",
                message=f"Case summary for session '{session_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return success_response(data=summary_doc)

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
