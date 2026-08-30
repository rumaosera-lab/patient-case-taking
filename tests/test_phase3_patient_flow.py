import pytest
from fastapi import status

from backend.utils.id_generator import (
    generate_patient_id,
    generate_session_id,
    generate_response_id,
)


def test_health_check(client):
    """
    Verify /api/v1/health returns healthy and database status.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
    assert body["data"]["service"] == "patient-case-taking-backend"


def test_root_endpoint(client):
    """
    Verify / root endpoint returns service info.
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert body["data"]["service"] == "Patient Case-Taking Software Backend"
    assert body["data"]["docs"] == "/docs"


def test_id_generators_sequential(mock_mongo):
    """
    Verify PAT-XXXXXX, SES-XXXXXX, RESP-XXXXXX sequential increment behavior.
    """
    db = mock_mongo

    # Patient IDs
    assert generate_patient_id(db) == "PAT-000001"
    db["patients"].insert_one({"patient_id": "PAT-000001"})
    assert generate_patient_id(db) == "PAT-000002"
    db["patients"].insert_one({"patient_id": "PAT-000002"})
    assert generate_patient_id(db) == "PAT-000003"

    # Session IDs
    assert generate_session_id(db) == "SES-000001"
    db["sessions"].insert_one({"session_id": "SES-000001"})
    assert generate_session_id(db) == "SES-000002"

    # Response IDs
    assert generate_response_id(db) == "RESP-000001"
    db["responses"].insert_one({"response_id": "RESP-000001"})
    assert generate_response_id(db) == "RESP-000002"


def test_patient_crud_and_validation(client):
    """
    Test patient creation, retrieval, and partial update.
    """
    # 1. Create Patient
    payload = {
        "name": "Rahul Sharma",
        "date_of_birth": "1981-04-12",
        "gender": "Male",
        "phone": "9876543210",
        "preferred_language": "hi",
        "abha_id": "ABHA-12345"
    }
    create_res = client.post("/api/v1/patients", json=payload)
    assert create_res.status_code == status.HTTP_201_CREATED
    create_body = create_res.json()
    assert create_body["success"] is True
    patient_id = create_body["data"]["patient_id"]
    assert patient_id.startswith("PAT-")
    assert create_body["data"]["name"] == "Rahul Sharma"
    assert create_body["data"]["preferred_language"] == "hi"

    # 2. Get Patient
    get_res = client.get(f"/api/v1/patients/{patient_id}")
    assert get_res.status_code == status.HTTP_200_OK
    get_body = get_res.json()
    assert get_body["success"] is True
    assert get_body["data"]["patient_id"] == patient_id
    assert get_body["data"]["phone"] == "9876543210"

    # 3. Patch / Update Patient
    update_payload = {
        "phone": "9876543211",
        "preferred_language": "mr"
    }
    patch_res = client.patch(f"/api/v1/patients/{patient_id}", json=update_payload)
    assert patch_res.status_code == status.HTTP_200_OK
    patch_body = patch_res.json()
    assert patch_body["success"] is True
    assert patch_body["data"]["phone"] == "9876543211"
    assert patch_body["data"]["preferred_language"] == "mr"
    assert patch_body["data"]["name"] == "Rahul Sharma"  # Unmodified field preserved


def test_active_session_handling_and_resumption(client):
    """
    Test active session detection and resumption logic:
    Patient checks active session -> None -> Create Session -> Check active session -> Resumes existing.
    """
    # 1. Create Patient
    patient_payload = {
        "name": "Priya Patel",
        "date_of_birth": "1990-06-20",
        "gender": "Female",
        "phone": "9812345678",
        "preferred_language": "en"
    }
    p_res = client.post("/api/v1/patients", json=patient_payload)
    patient_id = p_res.json()["data"]["patient_id"]

    # 2. Check active session initially (should be null)
    active_res1 = client.get(f"/api/v1/patients/{patient_id}/sessions/active")
    assert active_res1.status_code == status.HTTP_200_OK
    body1 = active_res1.json()
    assert body1["success"] is True
    assert body1["data"] is None
    assert "No active session found" in body1["message"]

    # 3. Create a new session
    session_payload = {
        "patient_id": patient_id,
        "department": "General Medicine"
    }
    s_res = client.post("/api/v1/sessions", json=session_payload)
    assert s_res.status_code == status.HTTP_201_CREATED
    session_data = s_res.json()["data"]
    session_id = session_data["session_id"]
    assert session_id.startswith("SES-")
    assert session_data["status"] == "IN_PROGRESS"

    # 4. Check active session again (should return the IN_PROGRESS session)
    active_res2 = client.get(f"/api/v1/patients/{patient_id}/sessions/active")
    assert active_res2.status_code == status.HTTP_200_OK
    body2 = active_res2.json()
    assert body2["success"] is True
    assert body2["data"]["session_id"] == session_id
    assert body2["data"]["status"] == "IN_PROGRESS"


def test_response_submission_and_retrieval(client):
    """
    Test submitting clinical intake responses and retrieving them in chronological order.
    """
    # 1. Create Patient and Session
    p_res = client.post("/api/v1/patients", json={
        "name": "Amit Kumar",
        "date_of_birth": "1975-11-05",
        "gender": "Male",
        "phone": "9123456789",
        "preferred_language": "hi"
    })
    patient_id = p_res.json()["data"]["patient_id"]

    s_res = client.post("/api/v1/sessions", json={
        "patient_id": patient_id,
        "department": "General Medicine"
    })
    session_id = s_res.json()["data"]["session_id"]

    # 2. Submit First Response (voice)
    resp1_payload = {
        "question_id": "Q-CHEST-001",
        "question_text": "What is your main problem today?",
        "answer_text": "Mujhe do din se chest mein pain hai.",
        "input_type": "voice",
        "language": "hi"
    }
    r1_res = client.post(f"/api/v1/sessions/{session_id}/responses", json=resp1_payload)
    assert r1_res.status_code == status.HTTP_201_CREATED
    r1_body = r1_res.json()
    assert r1_body["success"] is True
    assert r1_body["data"]["response_id"].startswith("RESP-")
    assert r1_body["data"]["question_id"] == "Q-CHEST-001"
    assert r1_body["data"]["input_type"] == "voice"
    resp1_id = r1_body["data"]["response_id"]

    # 3. Submit Second Response (text)
    resp2_payload = {
        "question_id": "Q-CHEST-002",
        "question_text": "Where exactly do you feel the pain?",
        "answer_text": "Central chest, radiating to left arm",
        "input_type": "text",
        "language": "en"
    }
    r2_res = client.post(f"/api/v1/sessions/{session_id}/responses", json=resp2_payload)
    assert r2_res.status_code == status.HTTP_201_CREATED
    r2_body = r2_res.json()
    assert r2_body["success"] is True
    assert r2_body["data"]["response_id"].startswith("RESP-")
    assert r2_body["data"]["response_id"] != resp1_id

    # 4. Retrieve Responses for Session
    get_resp_res = client.get(f"/api/v1/sessions/{session_id}/responses")
    assert get_resp_res.status_code == status.HTTP_200_OK
    get_resp_body = get_resp_res.json()
    assert get_resp_body["success"] is True
    assert len(get_resp_body["data"]) == 2
    assert get_resp_body["data"][0]["question_id"] == "Q-CHEST-001"
    assert get_resp_body["data"][1]["question_id"] == "Q-CHEST-002"

    # 5. Verify Session remains IN_PROGRESS
    session_res = client.get(f"/api/v1/sessions/{session_id}")
    assert session_res.status_code == status.HTTP_200_OK
    assert session_res.json()["data"]["status"] == "IN_PROGRESS"


def test_error_cases(client):
    """
    Test error handling and validation across patient and session APIs.
    """
    # Nonexistent patient
    get_p = client.get("/api/v1/patients/PAT-999999")
    assert get_p.status_code == status.HTTP_404_NOT_FOUND
    assert get_p.json()["error"]["code"] == "PATIENT_NOT_FOUND"

    patch_p = client.patch("/api/v1/patients/PAT-999999", json={"phone": "123"})
    assert patch_p.status_code == status.HTTP_404_NOT_FOUND
    assert patch_p.json()["error"]["code"] == "PATIENT_NOT_FOUND"

    active_p = client.get("/api/v1/patients/PAT-999999/sessions/active")
    assert active_p.status_code == status.HTTP_404_NOT_FOUND
    assert active_p.json()["error"]["code"] == "PATIENT_NOT_FOUND"

    # Session creation for nonexistent patient
    create_s = client.post("/api/v1/sessions", json={
        "patient_id": "PAT-999999",
        "department": "Cardiology"
    })
    assert create_s.status_code == status.HTTP_404_NOT_FOUND
    assert create_s.json()["error"]["code"] == "PATIENT_NOT_FOUND"

    # Nonexistent session
    get_s = client.get("/api/v1/sessions/SES-999999")
    assert get_s.status_code == status.HTTP_404_NOT_FOUND
    assert get_s.json()["error"]["code"] == "SESSION_NOT_FOUND"

    patch_s = client.patch("/api/v1/sessions/SES-999999", json={"status": "PROCESSING"})
    assert patch_s.status_code == status.HTTP_404_NOT_FOUND
    assert patch_s.json()["error"]["code"] == "SESSION_NOT_FOUND"

    # Response submission on nonexistent session
    resp_on_missing = client.post("/api/v1/sessions/SES-999999/responses", json={
        "question_id": "Q-001",
        "question_text": "Sample",
        "answer_text": "Sample",
        "input_type": "text",
        "language": "en"
    })
    assert resp_on_missing.status_code == status.HTTP_404_NOT_FOUND
    assert resp_on_missing.json()["error"]["code"] == "SESSION_NOT_FOUND"

    # Get responses on nonexistent session
    get_resp_missing = client.get("/api/v1/sessions/SES-999999/responses")
    assert get_resp_missing.status_code == status.HTTP_404_NOT_FOUND
    assert get_resp_missing.json()["error"]["code"] == "SESSION_NOT_FOUND"

    # Invalid request bodies
    # Missing required field in patient registration
    bad_patient = client.post("/api/v1/patients", json={"name": "Incomplete"})
    assert bad_patient.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Invalid input_type enum in response submission
    # 1. Create real patient and session
    p = client.post("/api/v1/patients", json={
        "name": "Test User",
        "date_of_birth": "2000-01-01",
        "gender": "Other",
        "phone": "9000000000",
        "preferred_language": "en"
    }).json()["data"]
    s = client.post("/api/v1/sessions", json={
        "patient_id": p["patient_id"],
        "department": "General Medicine"
    }).json()["data"]

    bad_resp = client.post(f"/api/v1/sessions/{s['session_id']}/responses", json={
        "question_id": "Q-001",
        "question_text": "Sample",
        "answer_text": "Sample",
        "input_type": "invalid_type",
        "language": "en"
    })
    assert bad_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Response submission on a completed/non-IN_PROGRESS session
    # 2. Update session to COMPLETED
    client.patch(f"/api/v1/sessions/{s['session_id']}", json={"status": "COMPLETED"})

    # 3. Attempt response submission on completed session
    resp_on_completed = client.post(f"/api/v1/sessions/{s['session_id']}/responses", json={
        "question_id": "Q-001",
        "question_text": "Sample",
        "answer_text": "Sample",
        "input_type": "text",
        "language": "en"
    })
    assert resp_on_completed.status_code == status.HTTP_400_BAD_REQUEST
    assert resp_on_completed.json()["error"]["code"] == "INVALID_REQUEST"


def test_complete_e2e_patient_flow(client):
    """
    End-to-end basic patient flow:
    1. Register patient
    2. Check active session (none found)
    3. Start session (IN_PROGRESS)
    4. Resume / verify active session returns same session
    5. Submit multiple intake responses
    6. Retrieve submitted responses and verify order and content
    7. Retrieve patient record
    8. Retrieve session record
    9. Verify session remains in IN_PROGRESS for downstream clinical intake
    """
    # Step 1: Patient Registration
    patient_res = client.post("/api/v1/patients", json={
        "name": "Sunita Verma",
        "date_of_birth": "1968-09-14",
        "gender": "Female",
        "phone": "9820011223",
        "preferred_language": "hi",
        "abha_id": "91-1234-5678-9012"
    })
    assert patient_res.status_code == 201
    patient_id = patient_res.json()["data"]["patient_id"]

    # Step 2: Check active session
    active_check1 = client.get(f"/api/v1/patients/{patient_id}/sessions/active")
    assert active_check1.status_code == 200
    assert active_check1.json()["data"] is None

    # Step 3: Create intake session
    session_res = client.post("/api/v1/sessions", json={
        "patient_id": patient_id,
        "department": "General Medicine"
    })
    assert session_res.status_code == 201
    session_id = session_res.json()["data"]["session_id"]

    # Step 4: Active session retrieval (resumption check)
    active_check2 = client.get(f"/api/v1/patients/{patient_id}/sessions/active")
    assert active_check2.status_code == 200
    assert active_check2.json()["data"]["session_id"] == session_id
    assert active_check2.json()["data"]["status"] == "IN_PROGRESS"

    # Step 5: Submit intake responses
    responses_to_submit = [
        {
            "question_id": "Q-001",
            "question_text": "What brings you to the hospital today?",
            "answer_text": "Mujhe 3 din se bukhar aur sardi hai.",
            "input_type": "voice",
            "language": "hi"
        },
        {
            "question_id": "Q-002",
            "question_text": "Do you have any cough?",
            "answer_text": "Yes, dry cough especially at night.",
            "input_type": "text",
            "language": "en"
        },
        {
            "question_id": "Q-003",
            "question_text": "Are you taking any medications?",
            "answer_text": "Paracetamol 650mg once yesterday.",
            "input_type": "touch",
            "language": "en"
        }
    ]

    submitted_ids = []
    for resp in responses_to_submit:
        sub_res = client.post(f"/api/v1/sessions/{session_id}/responses", json=resp)
        assert sub_res.status_code == 201
        data = sub_res.json()["data"]
        submitted_ids.append(data["response_id"])
        assert data["session_id"] == session_id
        assert data["question_id"] == resp["question_id"]

    # Step 6: Retrieve recorded responses
    get_resps = client.get(f"/api/v1/sessions/{session_id}/responses")
    assert get_resps.status_code == 200
    retrieved_data = get_resps.json()["data"]
    assert len(retrieved_data) == 3
    for i, item in enumerate(retrieved_data):
        assert item["response_id"] == submitted_ids[i]
        assert item["question_id"] == responses_to_submit[i]["question_id"]
        assert item["answer_text"] == responses_to_submit[i]["answer_text"]

    # Step 7: Retrieve patient information
    p_info = client.get(f"/api/v1/patients/{patient_id}")
    assert p_info.status_code == 200
    assert p_info.json()["data"]["name"] == "Sunita Verma"

    # Step 8: Retrieve session information
    s_info = client.get(f"/api/v1/sessions/{session_id}")
    assert s_info.status_code == 200
    assert s_info.json()["data"]["status"] == "IN_PROGRESS"
    assert s_info.json()["data"]["patient_id"] == patient_id
