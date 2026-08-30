import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.api import (
    health_router,
    patient_router,
    session_router,
    response_router,
    history_router,
    document_router,
    timeline_router,
    summary_router,
    interview_router,
    doctor_router,
    approval_router,
    auth_router,
)
from backend.database.connection import ensure_indexes
from backend.utils.responses import success_response

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Patient Case-Taking Software API",
    description="Pre-consultation clinical history and intake backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Ensure unique database indexes on startup
@app.on_event("startup")
def startup_event():
    ensure_indexes()

# Controlled CORS configuration for development
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register API v1 routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(patient_router, prefix="/api/v1")
app.include_router(session_router, prefix="/api/v1")
app.include_router(response_router, prefix="/api/v1")
app.include_router(history_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(timeline_router, prefix="/api/v1")
app.include_router(summary_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(doctor_router, prefix="/api/v1")
app.include_router(approval_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
def root():
    """
    Root endpoint returning basic service status.
    """
    return success_response(
        data={
            "service": "Patient Case-Taking Software Backend",
            "version": "1.0.0",
            "docs": "/docs",
            "api_prefix": "/api/v1"
        },
        message="Backend API is running"
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=True)
