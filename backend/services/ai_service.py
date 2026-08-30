from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIExtractionInput(BaseModel):
    question_id: str = Field(..., description="ID of question asked")
    question: str = Field(..., description="Question text")
    patient_answer: str = Field(..., description="Patient natural-language response")
    language: str = Field(default="en", description="Language code")
    expected_fields: List[str] = Field(default_factory=list, description="Fields to extract")


class AIExtractionOutput(BaseModel):
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Extracted clinical values")
    unmentioned_fields: List[str] = Field(default_factory=list, description="Fields not mentioned by patient")
    confidence: Optional[float] = Field(None, description="Extraction confidence score")


def extract_information_from_response(payload: AIExtractionInput) -> AIExtractionOutput:
    """
    Service interface/stub for Gemini information extraction from patient natural language answers.
    Follows Section 25, 26, 27 of docs/API_CONTRACTS.md.
    Never invents unmentioned medical facts.
    """
    # Clean stub: returns empty or unmentioned extraction without fabricating medical facts
    return AIExtractionOutput(
        extracted_fields={},
        unmentioned_fields=payload.expected_fields,
        confidence=None
    )


def generate_case_summary_text(
    patient_data: Dict[str, Any],
    history_data: Optional[Dict[str, Any]],
    responses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Service interface/stub for generating concise physician-facing case summary drafts.
    Follows Section 20 of docs/API_CONTRACTS.md.
    """
    # Extract chief complaint if available in responses or history
    chief_complaint_text = "No chief complaint recorded"
    hpi_text = "No history of present illness recorded"

    if responses:
        first_resp = responses[0]
        chief_complaint_text = first_resp.get("answer_text", chief_complaint_text)

    summary_text = f"Patient {patient_data.get('name', 'Unknown')} presents for consultation. Chief complaint: {chief_complaint_text}."

    return {
        "summary_text": summary_text,
        "structured_summary": {
            "chief_complaint": chief_complaint_text,
            "history_of_present_illness": hpi_text,
            "relevant_history": [],
            "current_medications": [],
            "relevant_investigations": [],
            "allergies": "No allergy reported"
        }
    }
