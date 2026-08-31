import os
from typing import Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

from pathlib import Path

# Load environment variables
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / "frontend" / ".env")
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME") or os.getenv("DB_NAME", "patient_case_taking")

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """
    Returns or initializes the PyMongo client.
    Reads MONGODB_URI from environment variables.
    """
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI environment variable is not set.")
        _client = MongoClient(uri)
    return _client


def get_db() -> Database:
    """
    Returns the MongoDB database instance.
    """
    client = get_client()
    db_name = os.getenv("MONGODB_DB_NAME") or os.getenv("DB_NAME", "patient_case_taking")
    return client[db_name]


def check_db_connection() -> bool:
    """
    Utility function to verify if MongoDB Atlas connection is active.
    """
    try:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            return False
        client = get_client()
        client.admin.command("ping")
        return True
    except Exception:
        return False


def ensure_indexes(db: Optional[Database] = None) -> bool:
    """
    Creates indexes across all application collections.
    Safely ignores connectivity errors if DB is unreachable.
    """
    try:
        if db is None:
            db = get_db()
        # Primary application ID unique indexes
        db["patients"].create_index("patient_id", unique=True)
        db["doctors"].create_index("doctor_id", unique=True)
        db["doctors"].create_index("email", unique=True)
        db["sessions"].create_index("session_id", unique=True)
        db["sessions"].create_index("patient_id")
        db["responses"].create_index("response_id", unique=True)
        db["responses"].create_index("session_id")
        db["clinical_histories"].create_index("history_id", unique=True)
        db["clinical_histories"].create_index("session_id", unique=True)
        db["documents"].create_index("document_id", unique=True)
        db["documents"].create_index("session_id")
        db["documents"].create_index("patient_id")
        db["extracted_information"].create_index("extraction_id", unique=True)
        db["extracted_information"].create_index("document_id")
        db["timeline_events"].create_index("event_id", unique=True)
        db["timeline_events"].create_index("patient_id")
        db["timeline_events"].create_index("session_id")
        db["case_summaries"].create_index("summary_id", unique=True)
        db["case_summaries"].create_index("session_id", unique=True)
        return True
    except Exception:
        return False
