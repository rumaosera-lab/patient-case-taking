"""
document_processor.py
----------------------
Responsibility:
    OCR raw text -> structured medical information matching ExtractedInformation
    contract (docs/API_CONTRACTS.md Section 18 & backend/models/extraction.py).
    Also provides the complete background processing pipeline:
    Document -> OCR -> Extraction -> Save ExtractedInformation -> Create TimelineEvents.

Design notes:
    - Conservative extraction: If a fact is not visibly present, it is omitted ([] or null).
    - Source traceability: Every extracted entity includes a valid source reference
      matching docs/API_CONTRACTS.md Section 16:
      {"type": "document", "source_id": document_id, "page": 1}.
    - Confidence is treated strictly as AI-estimated extraction confidence (0.0 to 1.0).
    - No diagnosis, no red-flag detection, no unsupported medical inference.
"""

import os
import re
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

from backend.services.ocr.ocr_service import extract_text_from_file

# Configure logging
logger = logging.getLogger(__name__)

# Load backend/.env
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Schema-compliant prompt matching ExtractedInformation contract
EXTRACTION_PROMPT_TEMPLATE = """You are a medical document extraction assistant.

Read the text below (OCR output from a medical document) and extract
ONLY the information explicitly present in it.

Rules:
- Do NOT infer, guess, or add anything not explicitly stated.
- Do NOT make medical diagnoses or clinical judgments.
- If a category is not mentioned, leave its list empty ([]).
- For medications, only extract medicine name, dosage, and frequency if explicitly written.
- For investigations, extract test name and result/value if written.
- Rate your own extraction confidence from 0.0 to 1.0 based solely on how legible and clear the source text was.
- Return valid JSON only. No explanations, no markdown code fences.

Return JSON in exactly this shape:
{{
  "diagnoses": [
    {{"name": "..."}}
  ],
  "medications": [
    {{"medicine": "...", "dosage": "...", "frequency": "..."}}
  ],
  "investigations": [
    {{"name": "...", "value": "..."}}
  ],
  "procedures": [
    {{"name": "..."}}
  ],
  "confidence": 0.0
}}

TEXT:
{raw_text}
"""

# Prompt for extracting dated clinical events for timeline generation
TIMELINE_PROMPT_TEMPLATE = """Read the medical document text below and list every
dated clinical event mentioned (e.g. diagnosis date, medication start date, lab test date,
procedure date, surgery, symptom onset).

Rules:
- Only include events with a specific date explicitly stated.
- If no date is found for an event, do not include it.
- event_date must be formatted as YYYY-MM-DD. If only month and year are available, format as YYYY-MM-01.
- event_type must be one of: diagnosis, medication, investigation, procedure, hospitalization, surgery, symptom, other.
- Return valid JSON only, as a list of event objects. No markdown code fences.

Return JSON in exactly this shape:
[
  {{"event_date": "YYYY-MM-DD", "event_type": "...", "title": "...", "description": "..."}}
]

TEXT:
{raw_text}
"""


def extract_medical_info(
    document_id: str,
    patient_id: Optional[str] = None,
    raw_text: str = "",
    filename: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Extracts structured medical information from OCR raw text.
    Matches the ExtractedInformation contract (docs/API_CONTRACTS.md Section 18).

    Args:
        document_id: Source document ID (e.g., DOC-000001).
        patient_id: Patient ID (e.g., PAT-000001). Optional.
        raw_text: Full OCR transcribed text from the document.
        filename: Optional original file name.

    Returns:
        Dict matching ExtractedInformation schema fields with source traceability.
    """
    resolved_patient_id = patient_id or kwargs.get("patientId") or "PAT-000001"
    if not raw_text and "text" in kwargs:
        raw_text = kwargs["text"]

    if not raw_text or not raw_text.strip():
        return {
            "document_id": document_id,
            "patient_id": resolved_patient_id,
            "diagnoses": [],
            "medications": [],
            "investigations": [],
            "procedures": [],
            "extracted_text": raw_text or "",
            "confidence": 0.0,
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured in environment.")

    prompt = EXTRACTION_PROMPT_TEMPLATE.format(raw_text=raw_text)
    candidate_models = [
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
    ]

    response_text = None
    seen_models = set()
    for model_name in candidate_models:
        if not model_name or model_name in seen_models:
            continue
        seen_models.add(model_name)
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                response_text = response.text
                break
        except Exception:
            continue

    if not response_text:
        raise ValueError("Gemini returned an empty response during medical extraction")

    data = _parse_json_response(response_text)
    if not isinstance(data, dict):
        raise ValueError("Gemini response was not a valid JSON object")

    # Attach official source reference to each extracted item (API_CONTRACTS.md Section 16)
    source_ref = {"type": "document", "source_id": document_id, "page": 1}

    def _format_items(items: Any, key_filter: List[str]) -> List[Dict[str, Any]]:
        if not isinstance(items, list):
            return []
        formatted = []
        for item in items:
            if isinstance(item, dict):
                cleaned_item = {k: v for k, v in item.items() if k in key_filter and v is not None}
                cleaned_item["source"] = source_ref
                formatted.append(cleaned_item)
            elif isinstance(item, str) and item.strip():
                formatted.append({"name": item.strip(), "source": source_ref})
        return formatted

    diagnoses = _format_items(data.get("diagnoses"), ["name", "description"])
    medications = _format_items(data.get("medications"), ["medicine", "dosage", "frequency", "duration"])
    investigations = _format_items(data.get("investigations"), ["name", "value", "unit", "reference_range"])
    procedures = _format_items(data.get("procedures"), ["name", "description"])

    raw_confidence = data.get("confidence")
    try:
        confidence = float(raw_confidence) if raw_confidence is not None else 0.85
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.85

    return {
        "document_id": document_id,
        "patient_id": resolved_patient_id,
        "diagnoses": diagnoses,
        "medications": medications,
        "investigations": investigations,
        "procedures": procedures,
        "extracted_text": raw_text,
        "confidence": confidence,
    }


def extract_timeline_candidates(document_id: str, raw_text: str) -> List[Dict[str, Any]]:
    """
    Extracts dated clinical event candidates from raw OCR text for timeline creation.
    Events without valid dates are excluded.
    """
    if not raw_text or not raw_text.strip():
        return []

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured in environment.")

    prompt = TIMELINE_PROMPT_TEMPLATE.format(raw_text=raw_text)
    candidate_models = [
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
    ]

    response_text = None
    seen_models = set()
    for model_name in candidate_models:
        if not model_name or model_name in seen_models:
            continue
        seen_models.add(model_name)
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                response_text = response.text
                break
        except Exception:
            continue

    if not response_text:
        return []

    try:
        candidates = _parse_json_response(response_text)
    except Exception:
        return []

    if not isinstance(candidates, list):
        return []

    allowed_types = {
        "diagnosis", "medication", "investigation", "procedure",
        "hospitalization", "surgery", "symptom", "other"
    }

    valid_events = []
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        event_date = str(cand.get("event_date", "")).strip()
        # Basic date sanity check (YYYY-MM-DD)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", event_date):
            continue

        raw_type = str(cand.get("event_type", "other")).lower().strip()
        event_type = raw_type if raw_type in allowed_types else "other"
        title = str(cand.get("title", "")).strip() or "Medical Event"
        description = str(cand.get("description", "")).strip() or f"Recorded from document {document_id}"

        valid_events.append({
            "event_date": event_date,
            "event_type": event_type,
            "title": title,
            "description": description,
        })

    return valid_events


def process_document_pipeline(
    document_id: str,
    file_bytes: Optional[bytes] = None,
    content_type: Optional[str] = None,
    filename: Optional[str] = None,
    db: Any = None
) -> Dict[str, Any]:
    """
    Executes the full document processing pipeline intended for FastAPI BackgroundTasks:
        1. Fetch document metadata from MongoDB
        2. Set processing_status = "PROCESSING"
        3. Perform OCR
        4. Perform Medical Information Extraction
        5. Save ExtractedInformation record with sequential ID
        6. Extract and save TimelineEvents with sequential IDs
        7. Set processing_status = "PROCESSED"
        On failure at any stage, sets processing_status = "FAILED".

    Args:
        document_id: Target document ID (e.g., DOC-000001).
        file_bytes: Binary content of document (if already in memory or fetched from S3).
        content_type: MIME type of the file.
        filename: Original file name.
        db: MongoDB Database instance (optional; retrieved via get_db() if omitted).

    Returns:
        Dict summarizing processing status and created IDs.
    """
    # Resolve database connection using existing project connection
    if db is None:
        try:
            from backend.database.connection import get_db
            db = get_db()
        except Exception as e:
            logger.error(f"Failed to obtain database connection: {e}")
            raise

    # Resolve ID generator functions using existing project utilities
    try:
        from backend.utils.id_generator import generate_extraction_id, generate_event_id
    except ImportError:
        # Fallback helper if imported in an isolated environment
        def generate_extraction_id(database):
            from backend.utils.id_generator import generate_extraction_id as gen_ext
            return gen_ext(database)

        def generate_event_id(database):
            from backend.utils.id_generator import generate_event_id as gen_evt
            return gen_evt(database)

    # 1. Fetch document record
    doc_record = db["documents"].find_one({"document_id": document_id})
    if not doc_record:
        raise ValueError(f"Document with ID '{document_id}' not found in database.")

    patient_id = doc_record.get("patient_id")
    session_id = doc_record.get("session_id")
    resolved_filename = filename or doc_record.get("file_name", "document")
    resolved_content_type = content_type or _infer_content_type(resolved_filename)

    # 2. Mark document as PROCESSING
    db["documents"].update_one(
        {"document_id": document_id},
        {"$set": {"processing_status": "PROCESSING"}}
    )

    try:
        # Check file bytes availability
        if not file_bytes:
            raise ValueError(f"No file bytes provided or available for document {document_id}")

        # 3. Perform OCR
        ocr_res = extract_text_from_file(
            document_id=document_id,
            filename=resolved_filename,
            file_bytes=file_bytes,
            content_type=resolved_content_type,
        )
        raw_text = ocr_res.full_text
        if not raw_text or not raw_text.strip():
            raise ValueError("OCR produced empty extracted text from document.")

        # 4. Perform Medical Extraction
        medical_info = extract_medical_info(
            document_id=document_id,
            patient_id=patient_id,
            raw_text=raw_text,
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        extraction_id = generate_extraction_id(db)

        extraction_record = {
            "extraction_id": extraction_id,
            "document_id": document_id,
            "patient_id": patient_id,
            "diagnoses": medical_info.get("diagnoses", []),
            "medications": medical_info.get("medications", []),
            "investigations": medical_info.get("investigations", []),
            "procedures": medical_info.get("procedures", []),
            "extracted_text": raw_text,
            "confidence": medical_info.get("confidence", 0.85),
            "created_at": now_iso,
        }

        # 5. Save ExtractedInformation to MongoDB
        db["extracted_information"].update_one(
            {"document_id": document_id},
            {"$set": extraction_record},
            upsert=True
        )

        # 6. Extract and save TimelineEvents
        timeline_candidates = extract_timeline_candidates(document_id=document_id, raw_text=raw_text)
        created_event_ids = []
        for cand in timeline_candidates:
            evt_id = generate_event_id(db)
            evt_record = {
                "event_id": evt_id,
                "patient_id": patient_id,
                "session_id": session_id,
                "event_date": cand["event_date"],
                "event_type": cand["event_type"],
                "title": cand["title"],
                "description": cand["description"],
                "source_type": "document",
                "source_id": document_id,
                "created_at": now_iso,
            }
            db["timeline_events"].insert_one(evt_record)
            created_event_ids.append(evt_id)

        # 7. Mark document as PROCESSED
        db["documents"].update_one(
            {"document_id": document_id},
            {"$set": {"processing_status": "PROCESSED"}}
        )

        return {
            "success": True,
            "document_id": document_id,
            "extraction_id": extraction_id,
            "timeline_events": created_event_ids,
            "processing_status": "PROCESSED"
        }

    except Exception as err:
        logger.error(f"Document processing failed for {document_id}: {err}")
        # Mark document as FAILED on error
        db["documents"].update_one(
            {"document_id": document_id},
            {"$set": {"processing_status": "FAILED"}}
        )
        raise


def _infer_content_type(filename: str) -> str:
    """Infers MIME type from filename extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    return "application/octet-stream"


def _parse_json_response(response_text: str) -> Any:
    """Safely extracts and parses JSON from Gemini text response."""
    cleaned = response_text.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Gemini response: {e}\nResponse was:\n{response_text}") from e