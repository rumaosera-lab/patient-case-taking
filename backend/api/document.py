import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from pymongo.errors import PyMongoError, DuplicateKeyError

from backend.database.connection import get_db
from backend.models.document import DocumentType, DocumentProcessingStatus
from backend.utils.responses import success_response, error_response
from backend.utils.id_generator import generate_document_id, generate_extraction_id
from backend.services.ocr_service import process_document_ocr
from backend.services.ai_service import extract_medical_information_from_document

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
ROOT_DIR = Path(__file__).resolve().parents[2]


@router.post("/sessions/{session_id}/documents", status_code=status.HTTP_201_CREATED)
def upload_document(
    session_id: str,
    document_type: DocumentType = Form(..., description="Category of medical document"),
    file: UploadFile = File(..., description="Uploaded medical document file")
):
    """
    Uploads a medical document for a session and triggers OCR/extraction.
    Follows Section 17.4 of docs/API_CONTRACTS.md.
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
        patient_id = session_doc.get("patient_id")
        doc_type_val = document_type.value if hasattr(document_type, "value") else str(document_type)
        file_name = file.filename or "uploaded_document"

        # Read file content safely
        file_bytes = file.file.read()
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        max_retries = 3
        for _ in range(max_retries):
            document_id = generate_document_id(db)
            saved_file_path = UPLOAD_DIR / f"{document_id}_{file_name}"
            try:
                with open(saved_file_path, "wb") as f:
                    f.write(file_bytes)
            except Exception:
                pass

            file_url = f"/api/v1/documents/{document_id}/file"
            doc_record = {
                "document_id": document_id,
                "patient_id": patient_id,
                "session_id": session_id,
                "file_name": file_name,
                "document_type": doc_type_val,
                "file_url": file_url,
                "processing_status": DocumentProcessingStatus.UPLOADED.value,
                "uploaded_at": now
            }

            try:
                db["documents"].insert_one(doc_record.copy())
                # Update session last_updated_at
                db["sessions"].update_one(
                    {"session_id": session_id},
                    {"$set": {"last_updated_at": now}}
                )

                # Process OCR & AI medical extraction if file bytes exist
                try:
                    ocr_res = process_document_ocr(document_id, file_bytes, file_name)
                    extraction_id = generate_extraction_id(db)
                    ai_ext = extract_medical_information_from_document(
                        document_id=document_id,
                        patient_id=patient_id,
                        document_type=doc_type_val,
                        extracted_text=ocr_res.extracted_text
                    )
                    extraction_record = {
                        "extraction_id": extraction_id,
                        "document_id": document_id,
                        "patient_id": patient_id,
                        "diagnoses": ai_ext.get("diagnoses", []),
                        "medications": ai_ext.get("medications", []),
                        "investigations": ai_ext.get("investigations", []),
                        "procedures": ai_ext.get("procedures", []),
                        "extracted_text": ocr_res.extracted_text,
                        "confidence": ai_ext.get("confidence", 0.9),
                        "created_at": now
                    }
                    db["extracted_information"].insert_one(extraction_record)

                    # Extract dated timeline events if text is present
                    try:
                        from backend.services.ocr.document_processor import extract_timeline_candidates
                        from backend.utils.id_generator import generate_event_id
                        if ocr_res.extracted_text:
                            candidates = extract_timeline_candidates(document_id, ocr_res.extracted_text)
                            for cand in candidates:
                                evt_id = generate_event_id(db)
                                db["timeline_events"].insert_one({
                                    "event_id": evt_id,
                                    "patient_id": patient_id,
                                    "session_id": session_id,
                                    "event_date": cand["event_date"],
                                    "event_type": cand["event_type"],
                                    "title": cand["title"],
                                    "description": cand["description"],
                                    "source_type": "document",
                                    "source_id": document_id,
                                    "created_at": now
                                })
                    except Exception:
                        pass
                except Exception:
                    # OCR/Extraction failure shouldn't crash document record creation
                    pass

                response_data = {
                    "document_id": document_id,
                    "file_name": doc_record["file_name"],
                    "document_type": doc_record["document_type"],
                    "processing_status": DocumentProcessingStatus.UPLOADED.value
                }
                return success_response(
                    data=response_data,
                    message="Document uploaded successfully",
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
        doc = db["documents"].find_one({"document_id": document_id}, {"_id": 0})
        if not doc:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message=f"Document with ID '{document_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not doc.get("file_url"):
            doc["file_url"] = f"/api/v1/documents/{document_id}/file"

        return success_response(data=doc)

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


@router.get("/documents/{document_id}/file")
def get_document_file(document_id: str):
    """
    Retrieves the raw document file (PDF, image, etc.) for viewing in the browser.
    """
    try:
        db = get_db()
        doc = db["documents"].find_one({"document_id": document_id})
        file_name = doc.get("file_name", "document.pdf") if doc else "demo_medical_report.pdf"

        candidate_paths = [
            UPLOAD_DIR / f"{document_id}_{file_name}",
            UPLOAD_DIR / f"{document_id}.pdf",
            UPLOAD_DIR / file_name,
            ROOT_DIR / file_name,
            ROOT_DIR / "demo_medical_report.pdf",
        ]

        found_path = None
        for p in candidate_paths:
            if p.exists() and p.is_file():
                found_path = p
                break

        if not found_path:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message=f"File for document '{document_id}' not found on server",
                status_code=status.HTTP_404_NOT_FOUND
            )

        mime_type, _ = mimetypes.guess_type(str(found_path))
        if not mime_type:
            if str(found_path).lower().endswith(".pdf"):
                mime_type = "application/pdf"
            elif str(found_path).lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif str(found_path).lower().endswith(".png"):
                mime_type = "image/png"
            else:
                mime_type = "application/octet-stream"

        return FileResponse(
            path=str(found_path),
            media_type=mime_type,
            filename=file_name,
            headers={
                "Content-Disposition": f'inline; filename="{file_name}"'
            }
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


@router.get("/documents/{document_id}/extraction")
def get_document_extraction(document_id: str):
    """
    Retrieves structured medical information extracted from a document.
    Matching docs/API_CONTRACTS.md Section 17.6 & Section 18.
    """
    try:
        db = get_db()
        doc = db["documents"].find_one({"document_id": document_id})
        if not doc:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message=f"Document with ID '{document_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        extraction = db["extracted_information"].find_one({"document_id": document_id}, {"_id": 0})
        if not extraction:
            now = datetime.now(timezone.utc).isoformat()
            extraction_id = generate_extraction_id(db)
            default_extraction = {
                "extraction_id": extraction_id,
                "document_id": document_id,
                "patient_id": doc.get("patient_id"),
                "diagnoses": [],
                "medications": [],
                "investigations": [],
                "procedures": [],
                "extracted_text": None,
                "confidence": None,
                "created_at": now
            }
            db["extracted_information"].insert_one(default_extraction.copy())
            extraction = db["extracted_information"].find_one({"document_id": document_id}, {"_id": 0})

        return success_response(data=extraction)

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
