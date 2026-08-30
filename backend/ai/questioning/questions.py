from backend.ai.questioning.models import (
    ClinicalField,
    ClinicalQuestionFramework,
    ComplaintTemplate,
    Condition,
    Question,
    QuestionInputType,
)

# ---------------------------------------------------------------------------
# Clinical history section mapping.
# Each ClinicalField value maps to the field of the clinical_histories
# collection (docs/API_CONTRACTS.md Section 15.1).
# ---------------------------------------------------------------------------

SECTION_BY_FIELD = {
    ClinicalField.CHIEF_COMPLAINT.value: "chief_complaint",
    ClinicalField.ONSET.value: "history_of_present_illness",
    ClinicalField.DURATION.value: "history_of_present_illness",
    ClinicalField.LOCATION.value: "history_of_present_illness",
    ClinicalField.CHARACTER.value: "history_of_present_illness",
    ClinicalField.RADIATION.value: "history_of_present_illness",
    ClinicalField.AGGRAVATING_FACTORS.value: "history_of_present_illness",
    ClinicalField.RELIEVING_FACTORS.value: "history_of_present_illness",
    ClinicalField.ASSOCIATED_SYMPTOMS.value: "history_of_present_illness",
    ClinicalField.PAST_MEDICAL_HISTORY.value: "past_medical_history",
    ClinicalField.PAST_SURGICAL_HISTORY.value: "past_surgical_history",
    ClinicalField.CURRENT_MEDICATIONS.value: "current_medications",
    ClinicalField.ALLERGIES.value: "allergies",
    ClinicalField.FAMILY_HISTORY.value: "family_history",
    ClinicalField.PERSONAL_HISTORY.value: "personal_history",
    ClinicalField.REVIEW_OF_SYSTEMS.value: "review_of_systems",
}

# Common "yes"/"no" tokens used by conditional follow-ups (en/hi/Hinglish).
YES_TOKENS = ["yes", "y", "haan", "ha", "haa", "ji haan", "hmm"]
NO_TOKENS = ["no", "n", "nahi", "nahin", "na", "noi", "ji nahi", "bilkul nahi"]


def _yes_no_question(
    question_id: str,
    field: ClinicalField,
    question_text: str,
    options: QuestionInputType = QuestionInputType.YES_NO,
) -> Question:
    return Question(
        question_id=question_id,
        field=field,
        question_text=question_text,
        input_type=options,
        required=True,
    )


def _text_question(
    question_id: str,
    field: ClinicalField,
    question_text: str,
    condition: Condition = None,
    options: QuestionInputType = QuestionInputType.TEXT,
    help_text: str = None,
) -> Question:
    return Question(
        question_id=question_id,
        field=field,
        question_text=question_text,
        input_type=options,
        required=True,
        condition=condition,
        help_text=help_text,
    )


def _yes_follow_up(question_id: str) -> Condition:
    return Condition(question_id=question_id, equals_any=list(YES_TOKENS))


CHIEF_COMPLAINT_QUESTION = Question(
    question_id="Q-CHIEF-001",
    field=ClinicalField.CHIEF_COMPLAINT,
    question_text="What is your main problem today?",
    input_type=QuestionInputType.VOICE,
    required=True,
    help_text="Tell me in one or two sentences what is bothering you most.",
)

# ---------------------------------------------------------------------------
# General clinical history questions.
# All clinical history sections defined by the project are covered here.
# ---------------------------------------------------------------------------

GENERAL_QUESTIONS = [
    _yes_no_question(
        "Q-GEN-PMH-YN",
        ClinicalField.PAST_MEDICAL_HISTORY,
        "Have you had any significant illnesses in the past?",
    ),
    _text_question(
        "Q-GEN-PMH-DETAIL",
        ClinicalField.PAST_MEDICAL_HISTORY,
        "Please tell me about your past illnesses and when they occurred.",
        condition=_yes_follow_up("Q-GEN-PMH-YN"),
    ),
    _yes_no_question(
        "Q-GEN-PSH-YN",
        ClinicalField.PAST_SURGICAL_HISTORY,
        "Have you undergone any surgery in the past?",
    ),
    _text_question(
        "Q-GEN-PSH-DETAIL",
        ClinicalField.PAST_SURGICAL_HISTORY,
        "Please tell me about your past surgeries, when they were done and for what reason.",
        condition=_yes_follow_up("Q-GEN-PSH-YN"),
    ),
    _yes_no_question(
        "Q-GEN-MEDS-YN",
        ClinicalField.CURRENT_MEDICATIONS,
        "Are you currently taking any medicines?",
    ),
    _text_question(
        "Q-GEN-MEDS-DETAIL",
        ClinicalField.CURRENT_MEDICATIONS,
        "Please list all the medicines you are currently taking.",
        condition=_yes_follow_up("Q-GEN-MEDS-YN"),
    ),
    _yes_no_question(
        "Q-GEN-ALLERGY-YN",
        ClinicalField.ALLERGIES,
        "Do you have any allergies to medicines, food, or anything else?",
    ),
    _text_question(
        "Q-GEN-ALLERGY-DETAIL",
        ClinicalField.ALLERGIES,
        "Please tell me what you are allergic to and what reaction you get.",
        condition=_yes_follow_up("Q-GEN-ALLERGY-YN"),
    ),
    _yes_no_question(
        "Q-GEN-FAMILY-YN",
        ClinicalField.FAMILY_HISTORY,
        "Do any of your family members have a significant medical condition?",
    ),
    _text_question(
        "Q-GEN-FAMILY-DETAIL",
        ClinicalField.FAMILY_HISTORY,
        "Please tell me about the medical conditions in your family.",
        condition=_yes_follow_up("Q-GEN-FAMILY-YN"),
    ),
    _yes_no_question(
        "Q-GEN-PERSONAL-YN",
        ClinicalField.PERSONAL_HISTORY,
        "Do you smoke, drink alcohol, or use tobacco?",
    ),
    _text_question(
        "Q-GEN-PERSONAL-DETAIL",
        ClinicalField.PERSONAL_HISTORY,
        "Please tell me about your smoking, alcohol or tobacco habits.",
        condition=_yes_follow_up("Q-GEN-PERSONAL-YN"),
    ),
    _text_question(
        "Q-GEN-ROS",
        ClinicalField.REVIEW_OF_SYSTEMS,
        "Do you have any other symptoms anywhere else in your body?",
        help_text="For example: fever, weight loss, difficulty passing urine, joint pain.",
    ),
]

# ---------------------------------------------------------------------------
# Complaint-specific HPI templates.
# The clinical framework decides which template applies from the chief
# complaint; the LLM is never allowed to drive the interview freely.
# ---------------------------------------------------------------------------

COMPLAINT_TEMPLATES = [
    ComplaintTemplate(
        complaint="chest pain",
        keywords=[
            "chest pain",
            "chest",
            "sine dard",
            "sine mein dard",
            "seene mein dard",
            "chhati mein dard",
            "chhati dard",
        ],
        questions=[
            _text_question(
                "Q-CHEST-001", ClinicalField.ONSET,
                "When did the chest pain first start?",
                help_text="For example: today morning, yesterday, or one week ago.",
            ),
            _text_question(
                "Q-CHEST-002", ClinicalField.DURATION,
                "How long have you had the pain?",
            ),
            _text_question(
                "Q-CHEST-003", ClinicalField.LOCATION,
                "Where exactly do you feel the pain?",
                help_text="For example: centre of the chest, left side, or behind the breastbone.",
            ),
            _text_question(
                "Q-CHEST-004", ClinicalField.CHARACTER,
                "How would you describe the pain, for example sharp, dull, pressing or burning?",
            ),
            _yes_no_question(
                "Q-CHEST-005", ClinicalField.RADIATION,
                "Does the pain move to another part of your body?",
            ),
            _text_question(
                "Q-CHEST-005-RAD", ClinicalField.RADIATION,
                "Where does the pain move to?",
                condition=_yes_follow_up("Q-CHEST-005"),
                help_text="For example: left arm, jaw, neck or back.",
            ),
            _text_question(
                "Q-CHEST-006", ClinicalField.AGGRAVATING_FACTORS,
                "What makes the pain worse?",
                help_text="For example: walking, exertion, eating or lying down.",
            ),
            _text_question(
                "Q-CHEST-007", ClinicalField.RELIEVING_FACTORS,
                "What makes the pain better?",
            ),
            _text_question(
                "Q-CHEST-008", ClinicalField.ASSOCIATED_SYMPTOMS,
                "Do you have any other symptoms with the pain, such as breathlessness or sweating?",
            ),
        ],
    ),
    ComplaintTemplate(
        complaint="abdominal pain",
        keywords=[
            "abdominal pain",
            "abdominal",
            "abdomen",
            "stomach pain",
            "stomach",
            "pet dard",
            "pet mein dard",
            "pet",
        ],
        questions=[
            _text_question(
                "Q-ABDO-001", ClinicalField.ONSET,
                "When did the abdominal pain first start?",
            ),
            _text_question(
                "Q-ABDO-002", ClinicalField.DURATION,
                "How long have you had the pain?",
            ),
            _text_question(
                "Q-ABDO-003", ClinicalField.LOCATION,
                "Where exactly do you feel the pain in your abdomen?",
                help_text="For example: upper, lower, right side, left side or all over.",
            ),
            _text_question(
                "Q-ABDO-004", ClinicalField.CHARACTER,
                "How would you describe the pain, for example cramping, burning or colicky?",
            ),
            _text_question(
                "Q-ABDO-005", ClinicalField.AGGRAVATING_FACTORS,
                "What makes the pain worse?",
                help_text="For example: eating, empty stomach, or pressing on the area.",
            ),
            _text_question(
                "Q-ABDO-006", ClinicalField.RELIEVING_FACTORS,
                "What makes the pain better?",
            ),
            _text_question(
                "Q-ABDO-007", ClinicalField.ASSOCIATED_SYMPTOMS,
                "Do you have nausea, vomiting, fever, or diarrhoea with the pain?",
            ),
        ],
    ),
    ComplaintTemplate(
        complaint="headache",
        keywords=[
            "headache",
            "head",
            "sir dard",
            "sar dard",
            "sir mein dard",
        ],
        questions=[
            _text_question(
                "Q-HEAD-001", ClinicalField.ONSET,
                "When did the headache first start?",
            ),
            _text_question(
                "Q-HEAD-002", ClinicalField.DURATION,
                "How long have you had the headache?",
            ),
            _text_question(
                "Q-HEAD-003", ClinicalField.LOCATION,
                "Where do you feel the headache, for example front, back, one side or all over?",
            ),
            _text_question(
                "Q-HEAD-004", ClinicalField.CHARACTER,
                "How would you describe the headache, for example throbbing, pressing or sharp?",
            ),
            _text_question(
                "Q-HEAD-005", ClinicalField.AGGRAVATING_FACTORS,
                "What makes the headache worse?",
                help_text="For example: light, noise, or working at a screen.",
            ),
            _text_question(
                "Q-HEAD-006", ClinicalField.RELIEVING_FACTORS,
                "What makes the headache better?",
            ),
            _text_question(
                "Q-HEAD-007", ClinicalField.ASSOCIATED_SYMPTOMS,
                "Do you have nausea, sensitivity to light, or any change in your vision?",
            ),
        ],
    ),
    ComplaintTemplate(
        complaint="back pain",
        keywords=[
            "back pain",
            "backache",
            "back",
            "kamar dard",
            "kamari dard",
            "kamar mein dard",
            "kamarthi",
        ],
        questions=[
            _text_question(
                "Q-BACK-001", ClinicalField.ONSET,
                "When did the back pain first start?",
            ),
            _text_question(
                "Q-BACK-002", ClinicalField.DURATION,
                "How long have you had the back pain?",
            ),
            _text_question(
                "Q-BACK-003", ClinicalField.LOCATION,
                "Where in your back is the pain, for example upper, lower or middle?",
            ),
            _text_question(
                "Q-BACK-004", ClinicalField.CHARACTER,
                "How would you describe the pain, for example aching, shooting or burning?",
            ),
            _text_question(
                "Q-BACK-005", ClinicalField.AGGRAVATING_FACTORS,
                "What makes the back pain worse?",
                help_text="For example: lifting, bending, sitting or standing for long.",
            ),
            _text_question(
                "Q-BACK-006", ClinicalField.RELIEVING_FACTORS,
                "What makes the back pain better?",
            ),
            _text_question(
                "Q-BACK-007", ClinicalField.ASSOCIATED_SYMPTOMS,
                "Do you have any numbness, tingling or weakness in your legs?",
            ),
        ],
    ),
    ComplaintTemplate(
        complaint="fever",
        keywords=[
            "fever",
            "bukhar",
            "bukhhar",
            "temperature",
            "taap",
        ],
        questions=[
            _text_question(
                "Q-FEVER-001", ClinicalField.ONSET,
                "When did the fever first start?",
            ),
            _text_question(
                "Q-FEVER-002", ClinicalField.DURATION,
                "How long have you had the fever?",
            ),
            _text_question(
                "Q-FEVER-003", ClinicalField.CHARACTER,
                "Is the fever continuous, or does it come and go?",
            ),
            _text_question(
                "Q-FEVER-004", ClinicalField.ASSOCIATED_SYMPTOMS,
                "Do you have cough, sore throat, body ache, or headache with the fever?",
            ),
        ],
    ),
    ComplaintTemplate(
        complaint="cough",
        keywords=[
            "cough",
            "khansi",
            "khasi",
            "khaansi",
        ],
        questions=[
            _text_question(
                "Q-COUGH-001", ClinicalField.ONSET,
                "When did the cough first start?",
            ),
            _text_question(
                "Q-COUGH-002", ClinicalField.DURATION,
                "How long have you had the cough?",
            ),
            _text_question(
                "Q-COUGH-003", ClinicalField.CHARACTER,
                "Is the cough dry, or do you bring up any sputum?",
            ),
            _text_question(
                "Q-COUGH-004", ClinicalField.AGGRAVATING_FACTORS,
                "What makes the cough worse?",
                help_text="For example: at night, when lying down, or after exertion.",
            ),
            _text_question(
                "Q-COUGH-005", ClinicalField.ASSOCIATED_SYMPTOMS,
                "Do you have fever, breathlessness, or chest pain with the cough?",
            ),
        ],
    ),
    ComplaintTemplate(
        complaint="diabetes",
        keywords=[
            "diabetes",
            "diabetic",
            "sugar",
            "sugur",
            "shugar",
            "madhumeh",
        ],
        questions=[
            _text_question(
                "Q-DM-001", ClinicalField.ONSET,
                "How long have you had diabetes?",
            ),
            _text_question(
                "Q-DM-002", ClinicalField.CHARACTER,
                "How is your blood sugar currently controlled?",
                help_text="For example: on tablets, insulin, or by diet alone.",
            ),
            _text_question(
                "Q-DM-003", ClinicalField.ASSOCIATED_SYMPTOMS,
                "Have you had any complications such as eye, kidney, or foot problems?",
            ),
        ],
    ),
    ComplaintTemplate(
        complaint="hypertension",
        keywords=[
            "hypertension",
            "blood pressure",
            "bloodpressure",
            "high bp",
            "bp",
        ],
        questions=[
            _text_question(
                "Q-HTN-001", ClinicalField.ONSET,
                "How long have you had high blood pressure?",
            ),
            _text_question(
                "Q-HTN-002", ClinicalField.CHARACTER,
                "How is your blood pressure currently controlled?",
                help_text="For example: on medicines, diet, or lifestyle changes.",
            ),
            _text_question(
                "Q-HTN-003", ClinicalField.ASSOCIATED_SYMPTOMS,
                "Have you had symptoms such as headaches, giddiness, or chest discomfort?",
            ),
        ],
    ),
]

FRAMEWORK = ClinicalQuestionFramework(
    chief_complaint_question=CHIEF_COMPLAINT_QUESTION,
    general_questions=GENERAL_QUESTIONS,
    complaint_templates=COMPLAINT_TEMPLATES,
    section_by_field=SECTION_BY_FIELD,
)