from datetime import datetime, timezone
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.summary import SummaryReviewStatus
from backend.services.ai_service import generate_case_summary_text
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_summary_id

router = APIRouter()


@router.post("/sessions/{session_id}/summary", status_code=status.HTTP_201_CREATED)
def generate_summary(session_id: str):
    """
    Generates an AI draft case summary for a session.
    Follows Section 20.3 of docs/API_CONTRACTS.md.
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

        patient_id = session_doc.get("patient_id")
        patient_doc = db["patients"].find_one({"patient_id": patient_id}, {"_id": 0}) or {}
        history_doc = db["clinical_histories"].find_one({"session_id": session_id}, {"_id": 0})
        responses = list(db["responses"].find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1))

        # Generate summary draft via AI service interface
        ai_draft = generate_case_summary_text(patient_doc, history_doc, responses)

        now = datetime.now(timezone.utc).isoformat()
        
        # Check if a summary already exists for this session
        existing_summary = db["case_summaries"].find_one({"session_id": session_id})
        if existing_summary:
            summary_id = existing_summary["summary_id"]
            db["case_summaries"].update_one(
                {"session_id": session_id},
                {"$set": {
                    "summary_text": ai_draft["summary_text"],
                    "structured_summary": ai_draft["structured_summary"],
                    "generated_at": now,
                    "review_status": SummaryReviewStatus.GENERATED.value,
                    "reviewed_by": None,
                    "doctor_notes": None,
                    "approved_at": None
                }}
            )
        else:
            max_retries = 3
            for _ in range(max_retries):
                summary_id = generate_summary_id(db)
                summary_record = {
                    "summary_id": summary_id,
                    "patient_id": patient_id,
                    "session_id": session_id,
                    "summary_text": ai_draft["summary_text"],
                    "structured_summary": ai_draft["structured_summary"],
                    "generated_at": now,
                    "reviewed_by": None,
                    "review_status": SummaryReviewStatus.GENERATED.value,
                    "doctor_notes": None,
                    "approved_at": None
                }

                try:
                    db["case_summaries"].insert_one(summary_record.copy())
                    break
                except DuplicateKeyError:
                    continue

        # Refresh session last_updated_at
        db["sessions"].update_one(
            {"session_id": session_id},
            {"$set": {"last_updated_at": now}}
        )

        saved_summary = db["case_summaries"].find_one({"session_id": session_id}, {"_id": 0})
        return success_response(
            data=saved_summary,
            status_code=status.HTTP_201_CREATED
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
    Follows Section 20.4 of docs/API_CONTRACTS.md.
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
