from fastapi import APIRouter, status
from pymongo.errors import PyMongoError

from backend.ai.questioning.engine import get_next_question
from backend.ai.questioning.questions import FRAMEWORK
from backend.database.connection import get_db
from backend.utils.responses import success_response, error_response

router = APIRouter()


@router.get("/sessions/{session_id}/next-question")
def get_next_question_for_session(session_id: str):
    """
    Returns the next clinical question for an active patient session.

    The questioning framework (backend/ai/questioning) selects the next
    question from the recorded responses using conditional logic; the LLM is
    not free to drive the interview. Returns `question: null` with
    `interview_complete: true` when all required fields are covered.
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
            {"_id": 0, "question_id": 1, "answer_text": 1}
        ).sort("timestamp", 1))

        result = get_next_question(responses)
        return success_response(data=result.model_dump())

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


@router.get("/clinical/questions")
def get_clinical_question_framework():
    """
    Returns the structured clinical question framework (question bank,
    complaint templates and section mapping) used to drive the interview.
    """
    return success_response(data=FRAMEWORK.model_dump())