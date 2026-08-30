import re
from pymongo.database import Database


def generate_patient_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe patient ID in PAT-XXXXXX format.
    Finds the highest existing PAT-XXXXXX in the collection and increments numeric suffix.
    """
    latest = db["patients"].find_one(
        {"patient_id": {"$regex": r"^PAT-\d+$"}},
        sort=[("patient_id", -1)]
    )
    if latest and "patient_id" in latest:
        match = re.search(r"^PAT-(\d+)$", latest["patient_id"])
        if match:
            current_num = int(match.group(1))
            return f"PAT-{current_num + 1:06d}"
    
    return "PAT-000001"


def generate_session_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe session ID in SES-XXXXXX format.
    Finds the highest existing SES-XXXXXX in the collection and increments numeric suffix.
    """
    latest = db["sessions"].find_one(
        {"session_id": {"$regex": r"^SES-\d+$"}},
        sort=[("session_id", -1)]
    )
    if latest and "session_id" in latest:
        match = re.search(r"^SES-(\d+)$", latest["session_id"])
        if match:
            current_num = int(match.group(1))
            return f"SES-{current_num + 1:06d}"

    return "SES-000001"


def generate_response_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe response ID in RESP-XXXXXX format.
    Finds the highest existing RESP-XXXXXX in the collection and increments numeric suffix.
    """
    latest = db["responses"].find_one(
        {"response_id": {"$regex": r"^RESP-\d+$"}},
        sort=[("response_id", -1)]
    )
    if latest and "response_id" in latest:
        match = re.search(r"^RESP-(\d+)$", latest["response_id"])
        if match:
            current_num = int(match.group(1))
            return f"RESP-{current_num + 1:06d}"

    return "RESP-000001"


def generate_history_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe clinical history ID in HIS-XXXXXX format.
    """
    latest = db["clinical_histories"].find_one(
        {"history_id": {"$regex": r"^HIS-\d+$"}},
        sort=[("history_id", -1)]
    )
    if latest and "history_id" in latest:
        match = re.search(r"^HIS-(\d+)$", latest["history_id"])
        if match:
            current_num = int(match.group(1))
            return f"HIS-{current_num + 1:06d}"

    return "HIS-000001"


def generate_document_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe document ID in DOC-XXXXXX format.
    """
    latest = db["documents"].find_one(
        {"document_id": {"$regex": r"^DOC-\d+$"}},
        sort=[("document_id", -1)]
    )
    if latest and "document_id" in latest:
        match = re.search(r"^DOC-(\d+)$", latest["document_id"])
        if match:
            current_num = int(match.group(1))
            return f"DOC-{current_num + 1:06d}"

    return "DOC-000001"


def generate_extraction_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe extraction ID in EXT-XXXXXX format.
    """
    latest = db["extracted_information"].find_one(
        {"extraction_id": {"$regex": r"^EXT-\d+$"}},
        sort=[("extraction_id", -1)]
    )
    if latest and "extraction_id" in latest:
        match = re.search(r"^EXT-(\d+)$", latest["extraction_id"])
        if match:
            current_num = int(match.group(1))
            return f"EXT-{current_num + 1:06d}"

    return "EXT-000001"


def generate_event_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe timeline event ID in EVT-XXXXXX format.
    """
    latest = db["timeline_events"].find_one(
        {"event_id": {"$regex": r"^EVT-\d+$"}},
        sort=[("event_id", -1)]
    )
    if latest and "event_id" in latest:
        match = re.search(r"^EVT-(\d+)$", latest["event_id"])
        if match:
            current_num = int(match.group(1))
            return f"EVT-{current_num + 1:06d}"

    return "EVT-000001"


def generate_summary_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe summary ID in SUM-XXXXXX format.
    """
    latest = db["case_summaries"].find_one(
        {"summary_id": {"$regex": r"^SUM-\d+$"}},
        sort=[("summary_id", -1)]
    )
    if latest and "summary_id" in latest:
        match = re.search(r"^SUM-(\d+)$", latest["summary_id"])
        if match:
            current_num = int(match.group(1))
            return f"SUM-{current_num + 1:06d}"

    return "SUM-000001"


def generate_doctor_id(db: Database) -> str:
    """
    Generates a sequential, prototype-safe doctor ID in DOC-XXXXXX format.
    """
    latest = db["doctors"].find_one(
        {"doctor_id": {"$regex": r"^DOC-\d+$"}},
        sort=[("doctor_id", -1)]
    )
    if latest and "doctor_id" in latest:
        match = re.search(r"^DOC-(\d+)$", latest["doctor_id"])
        if match:
            current_num = int(match.group(1))
            return f"DOC-{current_num + 1:06d}"

    return "DOC-000001"


