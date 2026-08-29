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
