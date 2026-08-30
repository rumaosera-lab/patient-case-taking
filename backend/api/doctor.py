from fastapi import APIRouter, status
from pymongo.errors import PyMongoError

from backend.database.connection import get_db
from backend.models.session import SessionStatus
from backend.utils.responses import success_response, error_response

router = APIRouter()


@router.get("/doctors/{doctor_id}/patients")
def get_doctor_patient_list(doctor_id: str):
    """
    Retrieves the list of patients for the doctor dashboard.
    Prioritizes sessions in READY_FOR_DOCTOR status.
    Follows Section 21.1 of docs/API_CONTRACTS.md.
    """
    try:
        db = get_db()
        
        # Retrieve all sessions sorted with READY_FOR_DOCTOR prioritized
        sessions = list(db["sessions"].find({}, {"_id": 0}).sort([
            ("last_updated_at", -1),
            ("started_at", -1)
        ]))

        patient_items = []
        seen_patients = set()

        # First collect READY_FOR_DOCTOR sessions
        ready_sessions = [s for s in sessions if s.get("status") == SessionStatus.READY_FOR_DOCTOR.value]
        other_sessions = [s for s in sessions if s.get("status") != SessionStatus.READY_FOR_DOCTOR.value]

        for s in (ready_sessions + other_sessions):
            pid = s.get("patient_id")
            if pid not in seen_patients:
                seen_patients.add(pid)
                patient_doc = db["patients"].find_one({"patient_id": pid}, {"_id": 0})
                if patient_doc:
                    patient_items.append({
                        "patient_id": pid,
                        "name": patient_doc.get("name"),
                        "gender": patient_doc.get("gender"),
                        "date_of_birth": patient_doc.get("date_of_birth"),
                        "phone": patient_doc.get("phone"),
                        "preferred_language": patient_doc.get("preferred_language"),
                        "session_id": s.get("session_id"),
                        "status": s.get("status"),
                        "department": s.get("department"),
                        "started_at": s.get("started_at"),
                        "last_updated_at": s.get("last_updated_at")
                    })

        # Also add any patients without sessions
        all_patients = list(db["patients"].find({}, {"_id": 0}))
        for p in all_patients:
            pid = p.get("patient_id")
            if pid not in seen_patients:
                seen_patients.add(pid)
                patient_items.append({
                    "patient_id": pid,
                    "name": p.get("name"),
                    "gender": p.get("gender"),
                    "date_of_birth": p.get("date_of_birth"),
                    "phone": p.get("phone"),
                    "preferred_language": p.get("preferred_language"),
                    "session_id": None,
                    "status": None,
                    "department": None,
                    "started_at": None,
                    "last_updated_at": None
                })

        return success_response(data=patient_items)

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


@router.get("/doctors/{doctor_id}/patients/{patient_id}/record")
def get_complete_patient_record(doctor_id: str, patient_id: str):
    """
    Retrieves the aggregated, doctor-oriented patient record.
    Follows Section 21.2 of docs/API_CONTRACTS.md.
    """
    try:
        db = get_db()
        
        # Verify patient exists
        patient_doc = db["patients"].find_one({"patient_id": patient_id}, {"_id": 0})
        if not patient_doc:
            return error_response(
                code="PATIENT_NOT_FOUND",
                message=f"Patient with ID '{patient_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Get latest session for patient
        latest_session = db["sessions"].find_one(
            {"patient_id": patient_id},
            {"_id": 0},
            sort=[("last_updated_at", -1), ("started_at", -1)]
        )

        session_id = latest_session.get("session_id") if latest_session else None

        # Get case summary if session exists
        case_summary = None
        relevant_history = {}
        if session_id:
            case_summary = db["case_summaries"].find_one({"session_id": session_id}, {"_id": 0})
            relevant_history = db["clinical_histories"].find_one({"session_id": session_id}, {"_id": 0}) or {}

        # Get timeline events (chronological)
        timeline = list(db["timeline_events"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort([("event_date", 1), ("created_at", 1)]))

        # Get documents
        documents = list(db["documents"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("uploaded_at", -1))

        record_data = {
            "patient": patient_doc,
            "current_session": latest_session or {},
            "case_summary": case_summary or {},
            "relevant_history": relevant_history,
            "timeline": timeline,
            "documents": documents
        }

        return success_response(data=record_data)

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
