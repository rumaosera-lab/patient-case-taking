from datetime import datetime, timezone
from fastapi import APIRouter, status, Form, UploadFile, File
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.document import DocumentType, DocumentProcessingStatus
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_document_id

router = APIRouter()


@router.post("/sessions/{session_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    session_id: str,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...)
):
    """
    Uploads document file metadata for a session.
    Matching docs/API_CONTRACTS.md Section 17.4.
    """
    try:
        db = get_db()
        
        # Verify session exists
        session_doc = db["sessions"].find_one({"session_id": session_id})
        if not session_doc:
            return error_response(
                code="SESSION_NOT_FOUND",
                message=f"Session with ID '{session_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        now = datetime.now(timezone.utc).isoformat()
        file_name = file.filename or "uploaded_document"
        patient_id = session_doc["patient_id"]

        max_retries = 3
        for _ in range(max_retries):
            doc_id = generate_document_id(db)
            doc_data = {
                "document_id": doc_id,
                "patient_id": patient_id,
                "session_id": session_id,
                "file_name": file_name,
                "document_type": document_type.value,
                "file_url": None,
                "processing_status": DocumentProcessingStatus.UPLOADED.value,
                "uploaded_at": now
            }

            try:
                db["documents"].insert_one(doc_data.copy())
                response_payload = {
                    "document_id": doc_id,
                    "file_name": file_name,
                    "document_type": document_type.value,
                    "processing_status": DocumentProcessingStatus.UPLOADED.value
                }
                return success_response(
                    data=response_payload,
                    status_code=status.HTTP_201_CREATED
                )
            except DuplicateKeyError:
                continue

        return error_response(
            code="DUPLICATE_RESOURCE",
            message="Failed to generate unique document ID due to high concurrency. Please try again.",
            status_code=status.HTTP_409_CONFLICT
        )

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


@router.get("/documents/{document_id}")
def get_document(document_id: str):
    """
    Retrieves document metadata by document_id.
    Matching docs/API_CONTRACTS.md Section 17.5.
    """
    try:
        db = get_db()
        doc_data = db["documents"].find_one({"document_id": document_id}, {"_id": 0})
        
        if not doc_data:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message=f"Document with ID '{document_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return success_response(data=doc_data)

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


@router.get("/documents/{document_id}/extraction")
def get_document_extraction(document_id: str):
    """
    Retrieves medical information extracted from a document.
    Matching docs/API_CONTRACTS.md Section 17.6 & Section 18.
    """
    try:
        db = get_db()
        
        # Verify document exists
        doc_data = db["documents"].find_one({"document_id": document_id})
        if not doc_data:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message=f"Document with ID '{document_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        extraction_data = db["extracted_information"].find_one({"document_id": document_id}, {"_id": 0})
        
        if not extraction_data:
            empty_extraction = {
                "extraction_id": None,
                "document_id": document_id,
                "patient_id": doc_data["patient_id"],
                "diagnoses": [],
                "medications": [],
                "investigations": [],
                "procedures": [],
                "extracted_text": None,
                "confidence": None,
                "created_at": None
            }
            return success_response(data=empty_extraction)

        return success_response(data=extraction_data)

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
