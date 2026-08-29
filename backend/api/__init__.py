from .health import router as health_router
from .patient import router as patient_router
from .session import router as session_router

__all__ = ["health_router", "patient_router", "session_router"]
