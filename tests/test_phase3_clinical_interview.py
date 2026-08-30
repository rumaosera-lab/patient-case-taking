import pytest
from fastapi import status

from backend.ai.questioning.engine import (
    detect_complaint,
    get_next_question,
    interpret_answer,
)
from backend.ai.questioning.models import InterpretationInput
from backend.ai.questioning.questions import FRAMEWORK


def _create_patient_and_session(client):
    p = client.post("/api/v1/patients", json={
        "name": "Clinical Interview User",
        "date_of_birth": "1990-01-01",
        "gender": "Male",
        "phone": "9876500000",
        "preferred_language": "hi"
    }).json()["data"]
    s = client.post("/api/v1/sessions", json={
        "patient_id": p["patient_id"],
        "department": "General Medicine"
    }).json()["data"]
    return p["patient_id"], s["session_id"]


def _submit(client, session_id, question_id, question_text, answer_text, input_type="text", language="en"):
    res = client.post(f"/api/v1/sessions/{session_id}/responses", json={
        "question_id": question_id,
        "question_text": question_text,
        "answer_text": answer_text,
        "input_type": input_type,
        "language": language
    })
    assert res.status_code == status.HTTP_201_CREATED
    return res.json()["data"]


def _next(client, session_id):
    res = client.get(f"/api/v1/sessions/{session_id}/next-question")
    assert res.status_code == status.HTTP_200_OK
    return res.json()["data"]


def test_framework_covers_all_clinical_history_fields(client):
    """
    The clinical question framework must cover every clinical history field
    defined by the project's data model.
    """
    res = client.get("/api/v1/clinical/questions")
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["chief_complaint_question"]["question_id"] == "Q-CHIEF-001"

    all_field_ids = set()
    for q in [data["chief_complaint_question"]] + data["general_questions"]:
        all_field_ids.add(q["field"])
    for template in data["complaint_templates"]:
        all_field_ids.update(q["field"] for q in template["questions"])

    required = {
        "chief_complaint",
        "onset",
        "duration",
        "location",
        "character",
        "radiation",
        "aggravating_factors",
        "relieving_factors",
        "associated_symptoms",
        "past_medical_history",
        "past_surgical_history",
        "current_medications",
        "allergies",
        "family_history",
        "personal_history",
        "review_of_systems",
    }
    assert required.issubset(all_field_ids)
    assert data["section_by_field"]["chief_complaint"] == "chief_complaint"
    assert data["section_by_field"]["duration"] == "history_of_present_illness"
    assert data["section_by_field"]["current_medications"] == "current_medications"


def test_next_question_begins_with_chief_complaint(client):
    """
    An empty interview must start with the chief complaint question.
    """
    _, session_id = _create_patient_and_session(client)
    data = _next(client, session_id)

    assert data["interview_complete"] is False
    assert data["question"]["question_id"] == "Q-CHIEF-001"
    assert data["question"]["field"] == "chief_complaint"
    assert data["question"]["input_type"] == "voice"


def test_next_question_detects_complaint_and_orders_hpi(client):
    """
    After the chief complaint, the framework must trigger the matching
    complaint template and ask its HPI questions in order.
    """
    _, session_id = _create_patient_and_session(client)

    # 1. Chief complaint -> chest pain template
    _submit(client, session_id, "Q-CHIEF-001", "What is your main problem today?",
            "Mujhe sine mein dard hai", input_type="voice", language="hi")
    data = _next(client, session_id)
    assert data["active_complaint"] == "chest pain"
    assert data["question"]["question_id"] == "Q-CHEST-001"
    assert data["question"]["field"] == "onset"

    # 2. Answer onset -> next is duration
    _submit(client, session_id, "Q-CHEST-001", "When did the chest pain first start?",
            "aaj subah", language="hi")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-CHEST-002"
    assert data["question"]["field"] == "duration"

    # 3. A 'yes' on the radiation gate triggers the radiation detail question
    _submit(client, session_id, "Q-CHEST-002", "How long have you had the pain?", "yesterday")
    data = _next(client, session_id)

    # Answer the remaining HPI questions (location, character, radiation gate)
    _submit(client, session_id, "Q-CHEST-003", "Where exactly do you feel the pain?", "centre")
    data = _next(client, session_id)
    _submit(client, session_id, "Q-CHEST-004", "How would you describe the pain?", "dull")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-CHEST-005"
    _submit(client, session_id, "Q-CHEST-005", "Does the pain move to another part of your body?",
            "yes", input_type="yes_no")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-CHEST-005-RAD"
    assert data["question"]["field"] == "radiation"

    # 4. After radiation detail, aggravating/relieving/associated follow
    _submit(client, session_id, "Q-CHEST-005-RAD", "Where does the pain move to?", "left arm")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-CHEST-006"
    data = _next(client, session_id)  # fetch again; same question expected
    assert data["question"]["question_id"] == "Q-CHEST-006"


def test_conditional_general_history_yes_no_gates(client):
    """
    Yes/no gates control follow-up detail questions: 'yes' asks for details,
    'no' skips them. All general sections are supported.
    """
    _, session_id = _create_patient_and_session(client)

    # Complete a non-matching chief complaint so the generic path is reached
    _submit(client, session_id, "Q-CHIEF-001", "What is your main problem today?",
            "thakan", language="hi", input_type="voice")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-GEN-PMH-YN"

    # 'haan' triggers past medical history details
    _submit(client, session_id, "Q-GEN-PMH-YN", "Have you had any significant illnesses in the past?",
            "haan", input_type="yes_no", language="hi")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-GEN-PMH-DETAIL"

    _submit(client, session_id, "Q-GEN-PMH-DETAIL", "Please tell me about your past illnesses.",
            "Diabetes since 5 years")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-GEN-PSH-YN"

    # 'nahi' skips surgery details
    _submit(client, session_id, "Q-GEN-PSH-YN", "Have you undergone any surgery in the past?",
            "nahi", input_type="yes_no", language="hi")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-GEN-MEDS-YN"

    # 'yes' triggers medication details
    _submit(client, session_id, "Q-GEN-MEDS-YN", "Are you currently taking any medicines?",
            "yes", input_type="yes_no")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-GEN-MEDS-DETAIL"

    _submit(client, session_id, "Q-GEN-MEDS-DETAIL", "Please list all the medicines you are currently taking.",
            "Glibenclamide 5mg")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-GEN-ALLERGY-YN"

    # no allergies -> skip detail
    _submit(client, session_id, "Q-GEN-ALLERGY-YN", "Do you have any allergies?",
            "no", input_type="yes_no")
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-GEN-FAMILY-YN"


def test_interview_completes_when_all_fields_covered(client):
    """
    When every required framework question has been answered the interview
    reports complete with question: null.
    """
    _, session_id = _create_patient_and_session(client)

    path = [
        ("Q-CHIEF-001", "voice", "chest pain", "en"),
        ("Q-CHEST-001", "text", "yesterday", "en"),
        ("Q-CHEST-002", "text", "1 day", "en"),
        ("Q-CHEST-003", "text", "centre", "en"),
        ("Q-CHEST-004", "text", "sharp", "en"),
        ("Q-CHEST-005", "yes_no", "no", "en"),
        ("Q-CHEST-006", "text", "walking", "en"),
        ("Q-CHEST-007", "text", "rest", "en"),
        ("Q-CHEST-008", "text", "none", "en"),
        ("Q-GEN-PMH-YN", "yes_no", "no", "en"),
        ("Q-GEN-PSH-YN", "yes_no", "no", "en"),
        ("Q-GEN-MEDS-YN", "yes_no", "no", "en"),
        ("Q-GEN-ALLERGY-YN", "yes_no", "no", "en"),
        ("Q-GEN-FAMILY-YN", "yes_no", "no", "en"),
        ("Q-GEN-PERSONAL-YN", "yes_no", "no", "en"),
        ("Q-GEN-ROS", "text", "no other complaints", "en"),
    ]

    questions = {
        "Q-CHIEF-001": "What is your main problem today?",
        "Q-CHEST-001": "When did the chest pain first start?",
        "Q-CHEST-002": "How long have you had the pain?",
        "Q-CHEST-003": "Where exactly do you feel the pain?",
        "Q-CHEST-004": "How would you describe the pain?",
        "Q-CHEST-005": "Does the pain move to another part of your body?",
        "Q-CHEST-006": "What makes the pain worse?",
        "Q-CHEST-007": "What makes the pain better?",
        "Q-CHEST-008": "Do you have any other symptoms with the pain?",
        "Q-GEN-PMH-YN": "Have you had any significant illnesses in the past?",
        "Q-GEN-PSH-YN": "Have you undergone any surgery in the past?",
        "Q-GEN-MEDS-YN": "Are you currently taking any medicines?",
        "Q-GEN-ALLERGY-YN": "Do you have any allergies?",
        "Q-GEN-FAMILY-YN": "Do any of your family members have a significant medical condition?",
        "Q-GEN-PERSONAL-YN": "Do you smoke, drink alcohol, or use tobacco?",
        "Q-GEN-ROS": "Do you have any other symptoms anywhere else in your body?",
    }

    # First question must be the chief complaint
    data = _next(client, session_id)
    assert data["question"]["question_id"] == "Q-CHIEF-001"

    for qid, input_type, answer, language in path:
        data = _next(client, session_id)
        assert data["question"]["question_id"] == qid, f"expected {qid}, got {data['question']['question_id']}"
        _submit(client, session_id, qid, questions[qid], answer, input_type=input_type, language=language)

    data = _next(client, session_id)
    assert data["interview_complete"] is True
    assert data["question"] is None
    assert "chief_complaint" in data["completed_fields"]
    assert "past_surgical_history" in data["completed_fields"]


def test_next_question_missing_session_404(client):
    """
    next-question on a nonexistent session returns SESSION_NOT_FOUND.
    """
    res = client.get("/api/v1/sessions/SES-999999/next-question")
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_detect_complaint_keywords():
    """
    detect_complaint must map on plain-English and Hindi/Hinglish chief complaints.
    """
    assert detect_complaint("I have chest pain since morning") == "chest pain"
    assert detect_complaint("Mujhe sine mein dard hai") == "chest pain"
    assert detect_complaint("bukhar aur khansi hai") == "fever"
    assert detect_complaint("sugar ki bimari hai") == "diabetes"
    assert detect_complaint("blood pressure high hai") == "hypertension"
    assert detect_complaint("mere kamar mein dard hai") == "back pain"
    assert detect_complaint("just feeling tired") is None


def test_interpret_answer_yes_no_and_duration():
    """
    Natural-language yes/no and duration answers are interpreted into the
    structured AI output schema with confidence and source references.
    """
    # Hindi negation -> "no"
    i1 = interpret_answer(InterpretationInput(
        question_id="Q-GEN-PERSONAL-YN",
        question="Do you smoke, drink alcohol, or use tobacco?",
        patient_answer="nahi",
        expected_fields=["personal_history"],
    ))
    assert i1.extracted_fields == {"personal_history": "no"}
    assert i1.interpreted_fields[0].confidence == 0.95
    assert i1.interpreted_fields[0].source.type == "patient_response"
    assert i1.interpreted_fields[0].source.question_id == "Q-GEN-PERSONAL-YN"

    # Hinglish duration with response id reference
    i2 = interpret_answer(InterpretationInput(
        question_id="Q-CHEST-002",
        question="How long have you had the pain?",
        patient_answer="Mujhe 2 din se ho raha hai",
        expected_fields=["duration"],
    ), response_id="RESP-000009")
    assert i2.extracted_fields == {"duration": "2 days"}
    assert i2.source.response_id == "RESP-000009"
    assert i2.confidence == 0.9

    # Unmentioned expected field is reported and not extracted
    i3 = interpret_answer(InterpretationInput(
        question_id="Q-CHEST-008",
        question="Do you have any other symptoms?",
        patient_answer="No, none",
        expected_fields=["associated_symptoms"],
    ))
    assert i3.extracted_fields == {}
    assert "associated_symptoms" in i3.unmentioned_fields


def test_get_next_question_rejects_empty_answers(client):
    """
    Direct engine check: a recorded question without a usable answer is not
    treated as covered.
    """
    result = get_next_question([{"question_id": "Q-CHIEF-001", "answer_text": ""}])
    assert result.interview_complete is False
    assert result.question.question_id == "Q-CHIEF-001"