import re
from pymongo.database import Database


def _generate_sequential_id(db: Database, collection_name: str, field_name: str, prefix: str) -> str:
    """
    Helper function to generate sequential IDs in PREFIX-XXXXXX format.
    Finds the highest existing PREFIX-XXXXXX in the collection and increments numeric suffix.
    """
    pattern = rf"^{prefix}-\d+$"
    latest = db[collection_name].find_one(
        {field_name: {"$regex": pattern}},
        sort=[(field_name, -1)]
    )
    if latest and field_name in latest:
        match = re.search(rf"^{prefix}-(\d+)$", latest[field_name])
        if match:
            current_num = int(match.group(1))
            return f"{prefix}-{current_num + 1:06d}"
    return f"{prefix}-000001"


def generate_patient_id(db: Database) -> str:
    return _generate_sequential_id(db, "patients", "patient_id", "PAT")


def generate_session_id(db: Database) -> str:
    return _generate_sequential_id(db, "sessions", "session_id", "SES")


def generate_response_id(db: Database) -> str:
    return _generate_sequential_id(db, "responses", "response_id", "RESP")


def generate_history_id(db: Database) -> str:
    return _generate_sequential_id(db, "clinical_histories", "history_id", "HIS")


def generate_document_id(db: Database) -> str:
    return _generate_sequential_id(db, "documents", "document_id", "DOC")


def generate_extraction_id(db: Database) -> str:
    return _generate_sequential_id(db, "extracted_information", "extraction_id", "EXT")


def generate_event_id(db: Database) -> str:
    return _generate_sequential_id(db, "timeline_events", "event_id", "EVT")


def generate_summary_id(db: Database) -> str:
    return _generate_sequential_id(db, "case_summaries", "summary_id", "SUM")
