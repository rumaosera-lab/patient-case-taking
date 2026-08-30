from .health import router as health_router
from .patient import router as patient_router
from .session import router as session_router
from .response import router as response_router
from .history import router as history_router
from .document import router as document_router
from .timeline import router as timeline_router
from .summary import router as summary_router
from .interview import router as interview_router
from .doctor import router as doctor_router
from .approval import router as approval_router
from .auth import router as auth_router

__all__ = [
    "health_router",
    "patient_router",
    "session_router",
    "response_router",
    "history_router",
    "document_router",
    "timeline_router",
    "summary_router",
    "interview_router",
    "doctor_router",
    "approval_router",
    "auth_router",
]
