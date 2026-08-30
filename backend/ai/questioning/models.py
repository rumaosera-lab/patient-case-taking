from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuestionInputType(str, Enum):
    """
    Supported question input modes.

    `text`/`yes_no`/`multiple_choice` follow the Clinical Question Contract
    (docs/API_CONTRACTS.md Section 24). `voice` and `touch` preserve the
    interaction types already defined in the Response contract.
    """

    TEXT = "text"
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    VOICE = "voice"
    TOUCH = "touch"


class ClinicalField(str, Enum):
    """
    Structured clinical fields the interview collects.

    The values mirror the clinical history fields in `backend/models/history.py`
    and the history_of_present_illness sub-fields named in
    docs/API_CONTRACTS.md Section 15.1.
    """

    CHIEF_COMPLAINT = "chief_complaint"

    # History of present illness (HPI) sub-fields
    ONSET = "onset"
    DURATION = "duration"
    LOCATION = "location"
    CHARACTER = "character"
    RADIATION = "radiation"
    AGGRAVATING_FACTORS = "aggravating_factors"
    RELIEVING_FACTORS = "relieving_factors"
    ASSOCIATED_SYMPTOMS = "associated_symptoms"

    # General clinical history sections
    PAST_MEDICAL_HISTORY = "past_medical_history"
    PAST_SURGICAL_HISTORY = "past_surgical_history"
    CURRENT_MEDICATIONS = "current_medications"
    ALLERGIES = "allergies"
    FAMILY_HISTORY = "family_history"
    PERSONAL_HISTORY = "personal_history"
    REVIEW_OF_SYSTEMS = "review_of_systems"


class Condition(BaseModel):
    """
    Conditional rule that decides whether a question should follow a previous
    answer. If `question_id` or `field` is provided, the condition only
    evaluates against that recorded answer.

    Semantics:
    - reference only -> met when the referenced question has been answered.
    - `equals` / `equals_any` -> met when the normalized answer matches.
    - `contains` -> met when the normalized answer contains the text.
    - no reference and no matcher -> the question is always asked.
    """

    question_id: Optional[str] = Field(
        None, description="Previous question whose answer controls this question"
    )
    field: Optional[ClinicalField] = Field(
        None, description="Clinical field whose recorded answer controls this question"
    )
    equals: Optional[str] = Field(None, description="Trigger when answer equals this (case-insensitive)")
    equals_any: Optional[List[str]] = Field(
        None, description="Trigger when answer equals any of these (case-insensitive)"
    )
    contains: Optional[str] = Field(
        None, description="Trigger when answer contains this text (case-insensitive)"
    )


class Question(BaseModel):
    """
    A single structured clinical question.

    Matches the Question Object in docs/API_CONTRACTS.md Section 24 plus the
    `condition` rule used by the adaptive questioning engine.
    """

    question_id: str = Field(..., description="Unique question identifier (e.g. Q-CHEST-003)")
    field: ClinicalField = Field(..., description="Clinical field this question collects")
    question_text: str = Field(..., description="Question displayed/read to the patient")
    input_type: QuestionInputType = Field(
        default=QuestionInputType.TEXT, description="Interaction mode (text, yes_no, ...)"
    )
    required: bool = Field(default=True, description="Whether the map expects this information")
    options: Optional[List[str]] = Field(None, description="Selectable options for touch/multiple-choice")
    condition: Optional[Condition] = Field(
        None, description="Conditional rule gating this follow-up question"
    )
    help_text: Optional[str] = Field(None, description="Optional clarification for the patient")


class ComplaintTemplate(BaseModel):
    """
    Complaint-specific questioning path. When the chief complaint matches this
    template, its questions are asked (in order) before general history.
    """

    complaint: str = Field(..., description="Canonical complaint name (e.g. 'chest pain')")
    keywords: List[str] = Field(..., description="Terms that trigger this template")
    questions: List[Question] = Field(..., description="Complaint-specific HPI questions in ask order")


class ClinicalQuestionFramework(BaseModel):
    """
    The full structured question bank that controls the interview.

    The framework (not the LLM) determines what information must be collected.
    """

    chief_complaint_question: Question = Field(..., description="Opening chief complaint question")
    general_questions: List[Question] = Field(
        ..., description="General clinical history questions (past/surgical/medications/allergies/...)"
    )
    complaint_templates: List[ComplaintTemplate] = Field(
        ..., description="Complaint-specific HPI questioning templates"
    )
    section_by_field: Dict[str, str] = Field(
        ..., description="Maps each ClinicalField value to its clinical history section"
    )


class NextQuestionResult(BaseModel):
    """
    Result of the next-question selection for a session.
    """

    question: Optional[Question] = Field(None, description="Next question to ask, or None when interview complete")
    interview_complete: bool = Field(..., description="True when all required framework questions are covered")
    active_complaint: Optional[str] = Field(None, description="Detected complaint template name, if any")
    completed_fields: List[str] = Field(
        default_factory=list, description="Clinical fields already covered by recorded responses"
    )


class AnswerSource(BaseModel):
    """
    Traceability reference to the answering response/question.
    Follows docs/API_CONTRACTS.md Section 16 (patient_response source).
    """

    type: str = "patient_response"
    response_id: Optional[str] = Field(None, description="Response identifier the answer came from")
    question_id: Optional[str] = Field(None, description="Question identifier the answer answered")


class InterpretedField(BaseModel):
    """
    One extracted clinical field/value with confidence and source reference.
    """

    field: ClinicalField = Field(..., description="Clinical field that was extracted")
    value: Any = Field(None, description="Extracted clinical value")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Extraction confidence (0-1)")
    source: Optional[AnswerSource] = Field(None, description="Originating response/question reference")


class InterpretationInput(BaseModel):
    """
    Controlled input for interpreting a natural-language patient answer.
    Matches the AI Information-Extraction input in docs/API_CONTRACTS.md
    Section 25.
    """

    question_id: str = Field(..., description="ID of the question that was asked")
    question: str = Field(..., description="Question text")
    patient_answer: str = Field(..., description="Patient natural-language response")
    language: str = Field(default="en", description="Language code (en, hi, mr)")
    expected_fields: List[ClinicalField] = Field(
        default_factory=list, description="Clinical fields the answer is expected to provide"
    )


class AnswerInterpretation(BaseModel):
    """
    Structured interpretation of a patient's natural-language answer.

    `extracted_fields` keeps the backward-compatible flat mapping from
    docs/API_CONTRACTS.md Section 25 ({field: value}). `interpreted_fields`
    additionally carries a per-field confidence and the originating
    response/question reference.
    """

    question_id: str = Field(..., description="Question identifier this interpretation answers")
    answer_text: Optional[str] = Field(None, description="Raw patient answer text")
    language: Optional[str] = Field("en", description="Language code of the answer")
    extracted_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Flat {field: value} mapping (contract-compatible)"
    )
    interpreted_fields: List[InterpretedField] = Field(
        default_factory=list, description="Per-field value/confidence/source details"
    )
    unmentioned_fields: List[str] = Field(
        default_factory=list, description="Expected fields not mentioned in the answer"
    )
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Overall interpretation confidence")
    source: Optional[AnswerSource] = Field(None, description="Originating response/question reference")