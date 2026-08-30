import re
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional

from backend.ai.questioning.models import (
    AnswerInterpretation,
    AnswerSource,
    ClinicalField,
    ClinicalQuestionFramework,
    Condition,
    ComplaintTemplate,
    InterpretationInput,
    InterpretedField,
    NextQuestionResult,
    Question,
    QuestionInputType,
)
from backend.ai.questioning.questions import FRAMEWORK, NO_TOKENS, YES_TOKENS

_YES = {"yes", "y", "haan", "ha", "haa", "ji haan", "hmm"}
_NO = {"no", "n", "nahi", "nahin", "na", "noi", "ji nahi", "bilkul nahi"}
_NEG_MULTI = ("ji nahi", "bilkul nahi", "noi ji")

_YES_NO_PREFIXES = (
    "do you ",
    "do ",
    "does ",
    "is ",
    "are ",
    "have you ",
    "have ",
    "has ",
    "did ",
    "can ",
    "could ",
    "are you ",
    "want ",
    "need ",
)

_DURATION_PATTERN = re.compile(
    r"(?P<n>\d+)\s*(?P<u>day|days|din|hour|hours|ghanta|week|weeks|hafte|month|months|mahina|year|years|sal|saal)",
    re.IGNORECASE,
)
_UNIT_STANDARD = {
    "day": "days",
    "days": "days",
    "din": "days",
    "hour": "hours",
    "hours": "hours",
    "ghanta": "hours",
    "week": "weeks",
    "weeks": "weeks",
    "hafte": "weeks",
    "month": "months",
    "months": "months",
    "mahina": "months",
    "year": "years",
    "years": "years",
    "sal": "years",
    "saal": "years",
}


def normalize(text: Any) -> str:
    """
    Normalizes answer/question text for matching: lowercase, strip and
    collapse whitespace.
    """
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text).strip().lower())


def build_question_index(
    framework: ClinicalQuestionFramework = FRAMEWORK,
) -> Dict[str, Question]:
    """Maps every question_id in the framework to its Question definition."""
    index: Dict[str, Question] = {}
    for question in _iter_all_questions(framework):
        index[question.question_id] = question
    return index


def _iter_all_questions(
    framework: ClinicalQuestionFramework,
) -> Iterable[Question]:
    yield framework.chief_complaint_question
    for template in framework.complaint_templates:
        yield from template.questions
    yield from framework.general_questions


def _record_answer(record: Any) -> Optional[str]:
    """Extracts the answer text from a response record (API stored shape)."""
    if isinstance(record, dict):
        return record.get("answer_text")
    return None


def _response_by_question(
    responses: List[Any],
) -> Dict[str, str]:
    """question_id -> latest answer_text among recorded responses."""
    by_question: Dict[str, str] = {}
    for record in responses:
        question_id = record.get("question_id") if isinstance(record, dict) else None
        if not question_id:
            continue
        answer = _record_answer(record)
        if answer is None:
            continue
        by_question[question_id] = str(answer)
    return by_question


def _response_by_field(
    responses: List[Any],
    index: Dict[str, Question],
) -> Dict[ClinicalField, str]:
    """ClinicalField -> latest answer_text among recorded responses."""
    by_field: Dict[ClinicalField, str] = {}
    for record in responses:
        question_id = record.get("question_id") if isinstance(record, dict) else None
        if not question_id:
            continue
        question = index.get(question_id)
        if question is None:
            continue
        answer = _record_answer(record)
        if answer is None:
            continue
        by_field[question.field] = str(answer)
    return by_field


def _yes_no_value(answer: Any) -> Optional[bool]:
    """Parses a yes/no styled answer into a boolean, or None when unclear."""
    norm = normalize(answer)
    if not norm:
        return None
    if any(norm.startswith(prefix) for prefix in _NEG_MULTI):
        return False
    first = norm.split(" ")[0]
    if first in _NO:
        return False
    if first in _YES:
        return True
    return None


def _answer_matches(
    answer: Optional[str],
    equals: Optional[str] = None,
    equals_any: Optional[List[str]] = None,
    contains: Optional[str] = None,
) -> bool:
    """Checks a conditional matcher against a recorded answer."""
    norm = normalize(answer)
    if not norm:
        return False
    if equals is not None:
        matcher = normalize(equals)
        return norm == matcher or norm.startswith(matcher + " ")
    if equals_any:
        for candidate in equals_any:
            matcher = normalize(candidate)
            if matcher and (norm == matcher or norm.startswith(matcher + " ")):
                return True
        return False
    if contains is not None:
        return normalize(contains) in norm
    return True


def is_condition_met(
    condition: Optional[Condition],
    answers_by_question: Dict[str, str],
    answers_by_field: Dict[ClinicalField, str],
) -> bool:
    """
    Evaluates whether a follow-up question's condition is satisfied by the
    recorded answers. A question with no condition is always asked.
    """
    if condition is None:
        return True
    if condition.question_id is None and condition.field is None:
        return True

    answer = None
    if condition.question_id is not None:
        answer = answers_by_question.get(condition.question_id)
    elif condition.field is not None:
        answer = answers_by_field.get(condition.field)

    if answer is None or not str(answer).strip():
        return False

    return _answer_matches(
        str(answer),
        equals=condition.equals,
        equals_any=condition.equals_any,
        contains=condition.contains,
    )


def is_field_covered(
    field: ClinicalField,
    responses: List[Any],
    index: Dict[str, Question],
) -> bool:
    """
    Returns True when the recorded responses already provide the clinical
    field's value. A 'yes' answer to a yes/no gate is NOT considered coverage
    because the corresponding detail question still needs to be asked.
    """
    for record in responses:
        question_id = record.get("question_id") if isinstance(record, dict) else None
        if not question_id:
            continue
        question = index.get(question_id)
        if question is None or question.field != field:
            continue
        answer = _record_answer(record)
        if question.input_type == QuestionInputType.YES_NO and _yes_no_value(answer) is True:
            continue
        if answer is None or not str(answer).strip():
            continue
        return True
    return False


def _find_template(
    complaint: str,
    framework: ClinicalQuestionFramework,
) -> Optional[ComplaintTemplate]:
    for template in framework.complaint_templates:
        if template.complaint == complaint:
            return template
    return None


def detect_complaint(
    chief_complaint_answer: Any,
    framework: ClinicalQuestionFramework = FRAMEWORK,
) -> Optional[str]:
    """
    Detects the complaint-specific template from the patient's chief complaint
    by keyword matching. Returns None when no template applies.
    """
    text = normalize(chief_complaint_answer)
    if not text:
        return None
    for template in framework.complaint_templates:
        for keyword in template.keywords:
            if normalize(keyword) in text:
                return template.complaint
    return None


def get_next_question(
    responses: List[Any],
    framework: ClinicalQuestionFramework = FRAMEWORK,
) -> NextQuestionResult:
    """
    Selects the next question for a clinical interview based on the recorded
    responses. The framework (not the LLM) decides the required information:

    1. begin with the chief complaint unless it is covered;
    2. if a complaint template matches, ask its HPI questions in order;
    3. then ask the general clinical history questions in order;
    4. skip questions whose field is already covered or whose condition is unmet;
    5. when nothing remains, the interview is complete.
    """
    index = build_question_index(framework)
    answers_by_question = _response_by_question(responses)
    answers_by_field = _response_by_field(responses, index)
    answered_question_ids = set(answers_by_question.keys())

    completed_fields = [
        field.value
        for field in ClinicalField
        if is_field_covered(field, responses, index)
    ]

    chief_question = framework.chief_complaint_question
    if not is_field_covered(chief_question.field, responses, index):
        return NextQuestionResult(
            question=chief_question,
            interview_complete=False,
            active_complaint=None,
            completed_fields=completed_fields,
        )

    chief_answer = answers_by_field.get(chief_question.field)
    active_complaint = detect_complaint(chief_answer, framework)

    order: List[Question] = []
    if active_complaint is not None:
        template = _find_template(active_complaint, framework)
        if template is not None:
            order.extend(template.questions)
    order.extend(framework.general_questions)

    for question in order:
        if question.question_id in answered_question_ids:
            continue
        if is_field_covered(question.field, responses, index):
            continue
        if not is_condition_met(
            question.condition,
            answers_by_question,
            answers_by_field,
        ):
            continue
        return NextQuestionResult(
            question=question,
            interview_complete=False,
            active_complaint=active_complaint,
            completed_fields=completed_fields,
        )

    return NextQuestionResult(
        question=None,
        interview_complete=True,
        active_complaint=active_complaint,
        completed_fields=completed_fields,
    )


# ---------------------------------------------------------------------------
# AI output schema helpers (deterministic, non-AI baseline).
# A real LLM (Gemini) replaces the rule-based extractor in a later phase.
# ---------------------------------------------------------------------------


def _looks_like_yes_no(question_text: Any) -> bool:
    norm = normalize(question_text)
    return any(norm.startswith(prefix) for prefix in _YES_NO_PREFIXES)


def _extract_single_field(
    field: ClinicalField,
    answer: str,
    question_text: str,
) -> tuple:
    """Rule-based helper extracting (value, confidence) for one expected field."""
    norm = normalize(answer)
    if not norm:
        return None, None

    if _looks_like_yes_no(question_text):
        value = _yes_no_value(answer)
        if value is None:
            return None, None
        return ("yes" if value else "no"), 0.95

    if field is ClinicalField.DURATION:
        match = _DURATION_PATTERN.search(norm)
        if match:
            unit = _UNIT_STANDARD.get(match.group("u").lower(), match.group("u").lower())
            return f"{match.group('n')} {unit}", 0.9

    return norm, 0.7


def interpret_answer(
    payload: InterpretationInput,
    response_id: Optional[str] = None,
) -> AnswerInterpretation:
    """
    Interprets a patient's natural-language answer into the structured AI
    output schema. Produces the contract-compatible `extracted_fields` mapping
    and the richer `interpreted_fields` with per-field confidence and source
    reference to the originating response/question.
    """
    source = AnswerSource(
        response_id=response_id,
        question_id=payload.question_id,
    )

    extracted: Dict[str, Any] = {}
    interpreted: List[InterpretedField] = []
    unmentioned: List[str] = []
    confidences: List[float] = []

    for field in payload.expected_fields:
        value, confidence = _extract_single_field(field, payload.patient_answer, payload.question)
        if value is None:
            unmentioned.append(field.value)
            continue
        extracted[field.value] = value
        interpreted.append(
            InterpretedField(
                field=field,
                value=value,
                confidence=confidence,
                source=source,
            )
        )
        if confidence is not None:
            confidences.append(float(confidence))

    overall = round(mean(confidences), 4) if confidences else None

    return AnswerInterpretation(
        question_id=payload.question_id,
        answer_text=payload.patient_answer,
        language=payload.language,
        extracted_fields=extracted,
        interpreted_fields=interpreted,
        unmentioned_fields=unmentioned,
        confidence=overall,
        source=source,
    )