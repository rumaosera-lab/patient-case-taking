from fastapi import APIRouter
from backend.database.connection import check_db_connection
from backend.utils.responses import success_response

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify backend service status and MongoDB connectivity.
    """
    db_connected = check_db_connection()
    status_data = {
        "status": "healthy",
        "service": "patient-case-taking-backend",
        "version": "1.0.0",
        "database": "connected" if db_connected else "disconnected"
    }
    return success_response(
        data=status_data,
        message="Backend service is running"
    )
