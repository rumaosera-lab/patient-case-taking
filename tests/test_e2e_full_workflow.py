import io
import pytest
from fastapi import status


def test_full_patient_to_doctor_e2e_workflow(client, mock_mongo):
    """
    End-to-end integration test validating the entire journey:
    Patient Registration -> Active Session -> Adaptive Questioning -> Responses ->
    Document Upload -> OCR/Extraction -> Timeline -> AI Summary ->
    READY_FOR_DOCTOR -> Doctor Login -> Dashboard List -> Full Record ->
    Doctor History Edit -> Doctor Approval -> REVIEWED.
    """
    # 1. Patient Registration (Section 10.1)
    patient_res = client.post("/api/v1/patients", json={
        "name": "Sunita Verma",
        "date_of_birth": "1988-11-23",
        "gender": "Female",
        "phone": "9876543210",
        "preferred_language": "hi",
        "abha_id": "ABHA-SUNITA-001"
    })
    assert patient_res.status_code == status.HTTP_201_CREATED
    patient = patient_res.json()["data"]
    patient_id = patient["patient_id"]
    assert patient_id.startswith("PAT-")

    # 2. Patient Login (Section 12.1)
    login_res = client.post("/api/v1/auth/patient/login", json={
        "phone": "9876543210",
        "password": "patient_secret"
    })
    assert login_res.status_code == status.HTTP_200_OK
    assert "access_token" in login_res.json()["data"]

    # 3. Create Session (Section 13.3)
    session_res = client.post("/api/v1/sessions", json={
        "patient_id": patient_id,
        "department": "General Medicine"
    })
    assert session_res.status_code == status.HTTP_201_CREATED
    session = session_res.json()["data"]
    session_id = session["session_id"]
    assert session["status"] == "IN_PROGRESS"

    # 4. Check Active Session (Section 13.6)
    active_res = client.get(f"/api/v1/patients/{patient_id}/sessions/active")
    assert active_res.status_code == status.HTTP_200_OK
    assert active_res.json()["data"]["session_id"] == session_id
    assert active_res.json()["data"]["status"] == "IN_PROGRESS"

    # 5. Clinical Question Framework & Next Question (Section 24)
    q_bank_res = client.get("/api/v1/clinical/questions")
    assert q_bank_res.status_code == status.HTTP_200_OK
    assert q_bank_res.json()["success"] is True

    next_q1 = client.get(f"/api/v1/sessions/{session_id}/next-question")
    assert next_q1.status_code == status.HTTP_200_OK
    assert next_q1.json()["data"]["interview_complete"] is False
    assert next_q1.json()["data"]["question"]["question_id"] == "Q-CHIEF-001"

    # 6. Submit Chief Complaint Response (Section 14.3)
    r1 = client.post(f"/api/v1/sessions/{session_id}/responses", json={
        "question_id": "Q-CHIEF-001",
        "question_text": "What is your main problem today?",
        "answer_text": "Mujhe do din se chest mein pain hai.",
        "input_type": "voice",
        "language": "hi"
    })
    assert r1.status_code == status.HTTP_201_CREATED
    r1_data = r1.json()["data"]
    assert r1_data["response_id"].startswith("RESP-")

    # Next question detects chest pain complaint
    next_q2 = client.get(f"/api/v1/sessions/{session_id}/next-question")
    assert next_q2.status_code == status.HTTP_200_OK
    assert next_q2.json()["data"]["active_complaint"] == "chest pain"

    # 7. Submit Duration / HPI response
    r2 = client.post(f"/api/v1/sessions/{session_id}/responses", json={
        "question_id": "Q-CHEST-001",
        "question_text": "When did the chest pain start?",
        "answer_text": "2 days ago",
        "input_type": "text",
        "language": "en"
    })
    assert r2.status_code == status.HTTP_201_CREATED

    # Retrieve all recorded responses (Section 14.4)
    all_responses = client.get(f"/api/v1/sessions/{session_id}/responses")
    assert all_responses.status_code == status.HTTP_200_OK
    assert len(all_responses.json()["data"]) == 2

    # 8. Clinical History Auto-initialization and Updating (Section 15)
    hist_get = client.get(f"/api/v1/sessions/{session_id}/history")
    assert hist_get.status_code == status.HTTP_200_OK
    assert hist_get.json()["data"]["history_id"].startswith("HIS-")

    hist_patch = client.patch(f"/api/v1/sessions/{session_id}/history", json={
        "chief_complaint": {
            "value": "chest pain",
            "source": {"type": "patient_response", "source_id": r1_data["response_id"]}
        },
        "history_of_present_illness": {
            "duration": {
                "value": "2 days",
                "source": {"type": "patient_response", "source_id": r2.json()["data"]["response_id"]}
            }
        },
        "allergies": []
    })
    assert hist_patch.status_code == status.HTTP_200_OK
    assert hist_patch.json()["data"]["chief_complaint"]["value"] == "chest pain"

    # 9. Document Upload & Extraction (Section 17 & 18)
    doc_bytes = b"Rx: Tab Amlodipine 5 mg once daily for blood pressure."
    files = {"file": ("prescription.pdf", io.BytesIO(doc_bytes), "application/pdf")}
    data = {"document_type": "prescription"}

    doc_upload = client.post(f"/api/v1/sessions/{session_id}/documents", files=files, data=data)
    assert doc_upload.status_code == status.HTTP_201_CREATED
    doc_id = doc_upload.json()["data"]["document_id"]
    assert doc_id.startswith("DOC-")

    doc_meta = client.get(f"/api/v1/documents/{doc_id}")
    assert doc_meta.status_code == status.HTTP_200_OK

    doc_ext = client.get(f"/api/v1/documents/{doc_id}/extraction")
    assert doc_ext.status_code == status.HTTP_200_OK
    assert doc_ext.json()["data"]["document_id"] == doc_id

    # 10. Timeline (Section 19)
    # Insert a prior ECG event for timeline verification
    mock_mongo["timeline_events"].insert_one({
        "event_id": "EVT-000001",
        "patient_id": patient_id,
        "session_id": session_id,
        "event_date": "2026-06-15",
        "event_type": "investigation",
        "title": "ECG",
        "description": "Routine ECG test",
        "source_type": "document",
        "source_id": doc_id,
        "created_at": "2026-06-15T10:00:00Z"
    })

    timeline_res = client.get(f"/api/v1/patients/{patient_id}/timeline")
    assert timeline_res.status_code == status.HTTP_200_OK
    assert len(timeline_res.json()["data"]["events"]) == 1

    # 11. AI Case Summary Generation (Section 20)
    sum_gen = client.post(f"/api/v1/sessions/{session_id}/summary")
    assert sum_gen.status_code == status.HTTP_201_CREATED
    sum_data = sum_gen.json()["data"]
    assert sum_data["summary_id"].startswith("SUM-")
    assert sum_data["review_status"] == "GENERATED"

    # 12. Transition Session to READY_FOR_DOCTOR
    trans_ready = client.patch(f"/api/v1/sessions/{session_id}", json={"status": "READY_FOR_DOCTOR"})
    assert trans_ready.status_code == status.HTTP_200_OK
    assert trans_ready.json()["data"]["status"] == "READY_FOR_DOCTOR"

    # 13. Doctor Login (Section 12.2)
    doc_login = client.post("/api/v1/auth/doctor/login", json={
        "email": "doctor@hospital.com",
        "password": "doctor_secure_pwd"
    })
    assert doc_login.status_code == status.HTTP_200_OK
    assert doc_login.json()["data"]["user"]["role"] == "doctor"

    # 14. Doctor Dashboard Patients (Section 21.1)
    doc_patients = client.get("/api/v1/doctors/DOC-000001/patients")
    assert doc_patients.status_code == status.HTTP_200_OK
    doc_list = doc_patients.json()["data"]
    matching_patient = next((p for p in doc_list if p["patient_id"] == patient_id), None)
    assert matching_patient is not None
    assert matching_patient["status"] == "READY_FOR_DOCTOR"

    # 15. Doctor Full Patient Record (Section 21.2)
    doc_record = client.get(f"/api/v1/doctors/DOC-000001/patients/{patient_id}/record")
    assert doc_record.status_code == status.HTTP_200_OK
    record_data = doc_record.json()["data"]
    assert record_data["patient"]["name"] == "Sunita Verma"
    assert record_data["current_session"]["session_id"] == session_id
    assert len(record_data["timeline"]) == 1
    assert len(record_data["documents"]) == 1

    # 16. Doctor Edits History (Section 22)
    doc_edit = client.patch(f"/api/v1/sessions/{session_id}/history", json={
        "current_medications": [
            {
                "medicine": "Amlodipine",
                "dosage": "5 mg",
                "frequency": "once daily",
                "source": {"type": "document", "source_id": doc_id, "page": 1}
            }
        ]
    })
    assert doc_edit.status_code == status.HTTP_200_OK
    assert len(doc_edit.json()["data"]["current_medications"]) == 1

    # 17. Doctor Approves Record (Section 23)
    approve_res = client.post(f"/api/v1/sessions/{session_id}/approve", json={
        "reviewed_by": "DOC-000001",
        "doctor_notes": "Prescription verified. Ready for consultation."
    })
    assert approve_res.status_code == status.HTTP_200_OK
    app_data = approve_res.json()["data"]
    assert app_data["status"] == "REVIEWED"
    assert app_data["review_status"] == "APPROVED"
    assert app_data["reviewed_by"] == "DOC-000001"
    assert app_data["approved_at"] is not None

    # Verify session status in DB is now REVIEWED
    session_final = client.get(f"/api/v1/sessions/{session_id}")
    assert session_final.status_code == status.HTTP_200_OK
    assert session_final.json()["data"]["status"] == "REVIEWED"
