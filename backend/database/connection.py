import os
from typing import Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "patient_case_taking")

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
    return client[DB_NAME]


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
