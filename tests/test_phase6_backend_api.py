import io
import pytest
from fastapi import status
from pydantic import ValidationError

from backend.models.document import DocumentType, DocumentProcessingStatus
from backend.models.history import SourceType
from backend.models.summary import SummaryReviewStatus
from backend.models.timeline import TimelineEventType
from backend.services.ai_service import (
    AIExtractionInput,
    extract_information_from_response,
    generate_case_summary_text,
)
from backend.services.ocr_service import process_document_ocr
from backend.utils.id_generator import (
    generate_patient_id,
    generate_session_id,
    generate_response_id,
    generate_history_id,
    generate_document_id,
    generate_extraction_id,
    generate_event_id,
    generate_summary_id,
    generate_doctor_id,
)


def test_health_and_root(client):
    """Test health check and root service discovery endpoints."""
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["success"] is True
    assert r_root.json()["data"]["api_prefix"] == "/api/v1"

    r_health = client.get("/api/v1/health")
    assert r_health.status_code == 200
    assert r_health.json()["data"]["status"] == "healthy"
    assert r_health.json()["data"]["service"] == "patient-case-taking-backend"


def test_id_generators_full_suite(mock_mongo):
    """Test sequential increments across all application entity ID formats."""
    db = mock_mongo

    assert generate_patient_id(db) == "PAT-000001"
    assert generate_session_id(db) == "SES-000001"
    assert generate_response_id(db) == "RESP-000001"
    assert generate_history_id(db) == "HIS-000001"
    assert generate_document_id(db) == "DOC-000001"
    assert generate_extraction_id(db) == "EXT-000001"
    assert generate_event_id(db) == "EVT-000001"
    assert generate_summary_id(db) == "SUM-000001"
    assert generate_doctor_id(db) == "DOC-000001"


def test_patient_and_session_full_lifecycle(client):
    """Test patient registration, profile updates, session creation, and valid status transitions."""
    # 1. Register Patient
    p_res = client.post("/api/v1/patients", json={
        "name": "Ananya Desai",
        "date_of_birth": "1992-03-15",
        "gender": "Female",
        "phone": "9876500001",
        "preferred_language": "mr",
        "abha_id": "ABHA-0001"
    })
    assert p_res.status_code == 201
    patient_id = p_res.json()["data"]["patient_id"]
    assert patient_id.startswith("PAT-")

    # 2. Get & Update Patient
    p_get = client.get(f"/api/v1/patients/{patient_id}")
    assert p_get.status_code == 200
    assert p_get.json()["data"]["name"] == "Ananya Desai"

    p_patch = client.patch(f"/api/v1/patients/{patient_id}", json={"phone": "9876500002"})
    assert p_patch.status_code == 200
    assert p_patch.json()["data"]["phone"] == "9876500002"

    # 3. Create Session
    s_res = client.post("/api/v1/sessions", json={
        "patient_id": patient_id,
        "department": "General Medicine"
    })
    assert s_res.status_code == 201
    session_id = s_res.json()["data"]["session_id"]
    assert session_id.startswith("SES-")
    assert s_res.json()["data"]["status"] == "IN_PROGRESS"

    # 4. Valid Status Transitions
    # IN_PROGRESS -> PROCESSING
    trans1 = client.patch(f"/api/v1/sessions/{session_id}", json={"status": "PROCESSING"})
    assert trans1.status_code == 200
    assert trans1.json()["data"]["status"] == "PROCESSING"

    # PROCESSING -> READY_FOR_DOCTOR
    trans2 = client.patch(f"/api/v1/sessions/{session_id}", json={"status": "READY_FOR_DOCTOR"})
    assert trans2.status_code == 200
    assert trans2.json()["data"]["status"] == "READY_FOR_DOCTOR"

    # Invalid status transition (READY_FOR_DOCTOR -> IN_PROGRESS is invalid)
    bad_trans = client.patch(f"/api/v1/sessions/{session_id}", json={"status": "IN_PROGRESS"})
    assert bad_trans.status_code == 400
    assert bad_trans.json()["error"]["code"] == "INVALID_REQUEST"


def test_clinical_history_apis(client):
    """Test retrieving and partially updating clinical history with source traceability."""
    # 1. Setup Patient and Session
    p = client.post("/api/v1/patients", json={
        "name": "Rohan Gupta",
        "date_of_birth": "1985-07-22",
        "gender": "Male",
        "phone": "9876500010",
        "preferred_language": "hi"
    }).json()["data"]
    s = client.post("/api/v1/sessions", json={
        "patient_id": p["patient_id"],
        "department": "Cardiology"
    }).json()["data"]
    session_id = s["session_id"]

    # 2. Get Initial Clinical History (auto-initializes default empty structure)
    h_res = client.get(f"/api/v1/sessions/{session_id}/history")
    assert h_res.status_code == 200
    h_body = h_res.json()["data"]
    assert h_body["history_id"].startswith("HIS-")
    assert h_body["session_id"] == session_id
    assert h_body["current_medications"] == []

    # 3. Patch Clinical History with Source Info
    patch_payload = {
        "chief_complaint": {
            "value": "chest pain",
            "source": {
                "type": "patient_response",
                "source_id": "RESP-000001"
            }
        },
        "current_medications": [
            {
                "medicine": "Amlodipine",
                "dosage": "5 mg",
                "frequency": "once daily",
                "source": {
                    "type": "document",
                    "source_id": "DOC-000001",
                    "page": 1
                }
            }
        ]
    }
    h_patch = client.patch(f"/api/v1/sessions/{session_id}/history", json=patch_payload)
    assert h_patch.status_code == 200
    patched_body = h_patch.json()["data"]
    assert patched_body["chief_complaint"]["value"] == "chest pain"
    assert len(patched_body["current_medications"]) == 1
    assert patched_body["current_medications"][0]["medicine"] == "Amlodipine"
    assert patched_body["current_medications"][0]["source"]["type"] == "document"

    # Nonexistent session error check
    h_missing = client.get("/api/v1/sessions/SES-999999/history")
    assert h_missing.status_code == 404
    assert h_missing.json()["error"]["code"] == "SESSION_NOT_FOUND"

    h_patch_missing = client.patch("/api/v1/sessions/SES-999999/history", json={"past_medical_history": []})
    assert h_patch_missing.status_code == 404
    assert h_patch_missing.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_document_upload_and_extraction_apis(client):
    """Test multipart document upload, metadata retrieval, and extraction retrieval."""
    # 1. Setup Patient and Session
    p = client.post("/api/v1/patients", json={
        "name": "Kavita Rao",
        "date_of_birth": "1978-12-05",
        "gender": "Female",
        "phone": "9876500020",
        "preferred_language": "en"
    }).json()["data"]
    s = client.post("/api/v1/sessions", json={
        "patient_id": p["patient_id"],
        "department": "General Medicine"
    }).json()["data"]
    session_id = s["session_id"]

    # 2. Upload Document via multipart/form-data
    file_content = b"%PDF-1.4 sample test prescription content"
    files = {"file": ("prescription.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"document_type": "prescription"}

    upload_res = client.post(f"/api/v1/sessions/{session_id}/documents", files=files, data=data)
    assert upload_res.status_code == 201
    upload_body = upload_res.json()["data"]
    document_id = upload_body["document_id"]
    assert document_id.startswith("DOC-")
    assert upload_body["file_name"] == "prescription.pdf"
    assert upload_body["processing_status"] == "UPLOADED"

    # 3. Get Document Metadata
    doc_get = client.get(f"/api/v1/documents/{document_id}")
    assert doc_get.status_code == 200
    assert doc_get.json()["data"]["document_id"] == document_id
    assert doc_get.json()["data"]["document_type"] == "prescription"

    # 4. Get Extraction
    ext_get = client.get(f"/api/v1/documents/{document_id}/extraction")
    assert ext_get.status_code == 200
    ext_data = ext_get.json()["data"]
    assert ext_data["extraction_id"].startswith("EXT-")
    assert ext_data["document_id"] == document_id
    assert ext_data["diagnoses"] == []
    assert ext_data["medications"] == []

    # Nonexistent document checks
    doc_missing = client.get("/api/v1/documents/DOC-999999")
    assert doc_missing.status_code == 404
    assert doc_missing.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"

    ext_missing = client.get("/api/v1/documents/DOC-999999/extraction")
    assert ext_missing.status_code == 404
    assert ext_missing.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_timeline_apis(client, mock_mongo):
    """Test retrieving chronological medical timeline events for a patient."""
    db = mock_mongo
    patient_id = "PAT-000001"
    db["patients"].insert_one({"patient_id": patient_id, "name": "Timeline User"})

    # Insert events with different dates
    db["timeline_events"].insert_many([
        {
            "event_id": "EVT-000002",
            "patient_id": patient_id,
            "session_id": "SES-000001",
            "event_date": "2026-06-15",
            "event_type": "investigation",
            "title": "ECG",
            "description": "ECG normal",
            "source_type": "document",
            "source_id": "DOC-000001",
            "created_at": "2026-06-15T10:00:00Z"
        },
        {
            "event_id": "EVT-000001",
            "patient_id": patient_id,
            "session_id": "SES-000001",
            "event_date": "2024-01-10",
            "event_type": "diagnosis",
            "title": "Hypertension",
            "description": "Diagnosed in 2024",
            "source_type": "patient_response",
            "source_id": "RESP-000001",
            "created_at": "2024-01-10T10:00:00Z"
        }
    ])

    timeline_res = client.get(f"/api/v1/patients/{patient_id}/timeline")
    assert timeline_res.status_code == 200
    events = timeline_res.json()["data"]["events"]
    assert len(events) == 2
    # Chronological sort check (2024 event comes first)
    assert events[0]["event_date"] == "2024-01-10"
    assert events[1]["event_date"] == "2026-06-15"

    # Nonexistent patient timeline
    tl_missing = client.get("/api/v1/patients/PAT-999999/timeline")
    assert tl_missing.status_code == 404
    assert tl_missing.json()["error"]["code"] == "PATIENT_NOT_FOUND"


def test_case_summary_apis(client):
    """Test case summary draft generation and retrieval."""
    p = client.post("/api/v1/patients", json={
        "name": "Deepak Mehta",
        "date_of_birth": "1970-04-10",
        "gender": "Male",
        "phone": "9876500030",
        "preferred_language": "en"
    }).json()["data"]
    s = client.post("/api/v1/sessions", json={
        "patient_id": p["patient_id"],
        "department": "General Medicine"
    }).json()["data"]
    session_id = s["session_id"]

    # Submit a response
    client.post(f"/api/v1/sessions/{session_id}/responses", json={
        "question_id": "Q-001",
        "question_text": "Complaint",
        "answer_text": "Fever for 3 days",
        "input_type": "text",
        "language": "en"
    })

    # Generate Summary
    sum_gen = client.post(f"/api/v1/sessions/{session_id}/summary")
    assert sum_gen.status_code == 201
    sum_data = sum_gen.json()["data"]
    assert sum_data["summary_id"].startswith("SUM-")
    assert sum_data["session_id"] == session_id
    assert sum_data["review_status"] == "GENERATED"
    assert "Fever for 3 days" in sum_data["summary_text"]

    # Get Summary
    sum_get = client.get(f"/api/v1/sessions/{session_id}/summary")
    assert sum_get.status_code == 200
    assert sum_get.json()["data"]["summary_id"] == sum_data["summary_id"]

    # Nonexistent session summary checks
    sum_missing = client.get("/api/v1/sessions/SES-999999/summary")
    assert sum_missing.status_code == 404
    assert sum_missing.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_doctor_apis_and_approval_flow(client):
    """Test doctor patient list, aggregated record retrieval, and approval workflow."""
    # 1. Setup Patient, Session, Summary
    p = client.post("/api/v1/patients", json={
        "name": "Manish Shah",
        "date_of_birth": "1965-02-18",
        "gender": "Male",
        "phone": "9876500040",
        "preferred_language": "hi"
    }).json()["data"]
    patient_id = p["patient_id"]

    s = client.post("/api/v1/sessions", json={
        "patient_id": patient_id,
        "department": "General Medicine"
    }).json()["data"]
    session_id = s["session_id"]

    # Transition to READY_FOR_DOCTOR
    client.patch(f"/api/v1/sessions/{session_id}", json={"status": "READY_FOR_DOCTOR"})

    # 2. Doctor Patient List
    doc_patients = client.get("/api/v1/doctors/DOC-000001/patients")
    assert doc_patients.status_code == 200
    p_list = doc_patients.json()["data"]
    assert len(p_list) >= 1
    assert p_list[0]["patient_id"] == patient_id
    assert p_list[0]["status"] == "READY_FOR_DOCTOR"

    # 3. Doctor Complete Patient Record
    rec_res = client.get(f"/api/v1/doctors/DOC-000001/patients/{patient_id}/record")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()["data"]
    assert rec_data["patient"]["name"] == "Manish Shah"
    assert rec_data["current_session"]["session_id"] == session_id
    assert "timeline" in rec_data
    assert "documents" in rec_data

    # 4. Doctor Approval
    app_res = client.post(f"/api/v1/sessions/{session_id}/approve", json={
        "reviewed_by": "DOC-000001",
        "doctor_notes": "Prescription approved, follow up in 1 week"
    })
    assert app_res.status_code == 200
    app_data = app_res.json()["data"]
    assert app_data["status"] == "REVIEWED"
    assert app_data["review_status"] == "APPROVED"
    assert app_data["reviewed_by"] == "DOC-000001"

    # 5. Prevent Duplicate Approval
    app_dup = client.post(f"/api/v1/sessions/{session_id}/approve")
    assert app_dup.status_code == 400
    assert app_dup.json()["error"]["code"] == "INVALID_REQUEST"


def test_auth_reserved_stubs(client):
    """Test reserved authentication contract endpoints."""
    # Patient login stub
    p_login = client.post("/api/v1/auth/patient/login", json={
        "phone": "9876543210",
        "password": "secret_password"
    })
    assert p_login.status_code == 200
    p_data = p_login.json()["data"]
    assert "access_token" in p_data
    assert p_data["user"]["role"] == "patient"

    # Doctor login stub
    d_login = client.post("/api/v1/auth/doctor/login", json={
        "email": "doctor@hospital.com",
        "password": "doctor_password"
    })
    assert d_login.status_code == 200
    d_data = d_login.json()["data"]
    assert "access_token" in d_data
    assert d_data["user"]["role"] == "doctor"


def test_ai_and_ocr_services_interfaces():
    """Test AI and OCR service stubs direct functions and contracts."""
    # AI Extraction Stub test
    ai_in = AIExtractionInput(
        question_id="Q-001",
        question="How long have you had pain?",
        patient_answer="Two days",
        expected_fields=["duration"]
    )
    ai_out = extract_information_from_response(ai_in)
    assert ai_out.unmentioned_fields == ["duration"]
    assert ai_out.extracted_fields == {}

    # Case Summary generator helper test
    summary_out = generate_case_summary_text(
        patient_data={"name": "Test Name"},
        history_data=None,
        responses=[{"answer_text": "Chest pain"}]
    )
    assert "Chest pain" in summary_out["summary_text"]
    assert summary_out["structured_summary"]["chief_complaint"] == "Chest pain"

    # OCR stub test
    ocr_out = process_document_ocr("DOC-000001", b"content", "doc.pdf")
    assert ocr_out.document_id == "DOC-000001"
    assert ocr_out.extracted_text is None
    assert ocr_out.pages == []


def test_enum_validations():
    """Verify enum models enforce contracted enum values only."""
    assert DocumentType.PRESCRIPTION == "prescription"
    assert DocumentProcessingStatus.UPLOADED == "UPLOADED"
    assert SummaryReviewStatus.APPROVED == "APPROVED"
    assert SourceType.DOCUMENT == "document"
    assert TimelineEventType.INVESTIGATION == "investigation"
