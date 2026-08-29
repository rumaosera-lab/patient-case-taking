from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.summary import CaseSummaryCreate, SummaryReviewStatus, StructuredSummary
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
        else:
            # Default draft summary structure matching contract example
            default_structured = StructuredSummary(
                chief_complaint="Pending clinical history collection",
                history_of_present_illness="Pending intake completion",
                relevant_history=[],
                current_medications=[],
                relevant_investigations=[],
                allergies="No allergy reported"
            ).model_dump()

            summary_data = {
                "patient_id": patient_id,
                "session_id": session_id,
                "summary_text": "Draft case summary created.",
                "structured_summary": default_structured
            }

        summary_data["patient_id"] = patient_id
        summary_data["session_id"] = session_id
        summary_data["generated_at"] = now
        summary_data["reviewed_by"] = None
        summary_data["review_status"] = SummaryReviewStatus.GENERATED.value
        summary_data["doctor_notes"] = None
        summary_data["approved_at"] = None

        max_retries = 3
        for _ in range(max_retries):
            summary_id = generate_summary_id(db)
            summary_data["summary_id"] = summary_id

            try:
                db["case_summaries"].insert_one(summary_data.copy())
                # Return created summary object excluding _id
                summary_data.pop("_id", None)
                return success_response(
                    data=summary_data,
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
                message=f"Summary for session '{session_id}' not found",
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
