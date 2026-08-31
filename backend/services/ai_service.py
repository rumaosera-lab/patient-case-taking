import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / "frontend" / ".env")
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")
load_dotenv()


class AIExtractionInput(BaseModel):
    question_id: str = Field(..., description="ID of question asked")
    question: str = Field(..., description="Question text")
    patient_answer: str = Field(..., description="Patient natural-language response")
    language: str = Field(default="en", description="Language code")
    expected_fields: List[str] = Field(default_factory=list, description="Fields to extract")


class AIExtractionOutput(BaseModel):
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Extracted clinical values")
    unmentioned_fields: List[str] = Field(default_factory=list, description="Fields not mentioned by patient")
    confidence: Optional[float] = Field(None, description="Extraction confidence score")


def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def extract_information_from_response(payload: AIExtractionInput) -> AIExtractionOutput:
    """
    Extracts structured clinical information from patient natural language answers.
    Follows Section 25, 26, 27 of docs/API_CONTRACTS.md.
    Never invents unmentioned medical facts.
    """
    client = _get_gemini_client()
    if client:
        try:
            prompt = (
                f"You are a medical intake AI assistant. Extract structured clinical entities from the patient's answer.\n"
                f"Question ID: {payload.question_id}\n"
                f"Question: {payload.question}\n"
                f"Patient Answer: {payload.patient_answer}\n"
                f"Language: {payload.language}\n"
                f"Expected Fields: {json.dumps(payload.expected_fields)}\n\n"
                f"RULES:\n"
                f"1. Only extract information explicitly stated in the answer.\n"
                f"2. DO NOT diagnose or fabricate facts.\n"
                f"3. Return JSON object with keys:\n"
                f"   - extracted_fields: dictionary of field_name -> extracted_value\n"
                f"   - unmentioned_fields: list of expected fields not mentioned\n"
                f"   - confidence: float between 0.0 and 1.0\n"
            )
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=dict(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            return AIExtractionOutput(
                extracted_fields=data.get("extracted_fields", {}),
                unmentioned_fields=data.get("unmentioned_fields", []),
                confidence=data.get("confidence", 0.95)
            )
        except Exception:
            pass

    # Clean fallback / default interface matching contract
    return AIExtractionOutput(
        extracted_fields={},
        unmentioned_fields=payload.expected_fields,
        confidence=None
    )


def extract_medical_information_from_document(
    document_id: str,
    patient_id: str,
    document_type: str,
    extracted_text: Optional[str]
) -> Dict[str, Any]:
    """
    Extracts structured medical entities (medications, diagnoses, investigations, procedures)
    from OCR text of a medical document.
    Follows Section 18 of docs/API_CONTRACTS.md.
    """
    if not extracted_text or not extracted_text.strip():
        return {
            "diagnoses": [],
            "medications": [],
            "investigations": [],
            "procedures": [],
            "confidence": 0.9
        }

    client = _get_gemini_client()
    if client:
        try:
            prompt = (
                f"You are a clinical document parser. Extract medical information from this document text:\n"
                f"Document Type: {document_type}\n"
                f"Document ID: {document_id}\n\n"
                f"Text:\n{extracted_text}\n\n"
                f"Return a JSON object with:\n"
                f"- diagnoses: list of strings (only if explicitly present)\n"
                f"- medications: list of objects with keys: medicine, dosage, frequency, source (type: 'document', source_id: '{document_id}', page: 1)\n"
                f"- investigations: list of strings\n"
                f"- procedures: list of strings\n"
                f"- confidence: float between 0.0 and 1.0\n"
            )
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=dict(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception:
            pass

    # Regex/Deterministic fallback for common medication formats in prescription text
    medications = []
    lines = extracted_text.splitlines()
    for line in lines:
        match = re.search(r"(?:tab|cap|syrup|inj)?\.?\s*([A-Za-z]+)\s+(\d+\s*(?:mg|ml|gm|mcg))\s*(.*)", line, re.IGNORECASE)
        if match:
            med_name = match.group(1).strip()
            dosage = match.group(2).strip()
            freq = match.group(3).strip() or "as directed"
            medications.append({
                "medicine": med_name,
                "dosage": dosage,
                "frequency": freq,
                "source": {
                    "type": "document",
                    "source_id": document_id,
                    "page": 1
                }
            })

    return {
        "diagnoses": [],
        "medications": medications,
        "investigations": [],
        "procedures": [],
        "confidence": 0.85 if medications else 0.5
    }


def generate_case_summary_text(
    patient_data: Dict[str, Any],
    history_data: Optional[Dict[str, Any]],
    responses: List[Dict[str, Any]],
    extracted_docs: Optional[List[Dict[str, Any]]] = None,
    timeline_events: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generates a concise physician-facing case summary draft aggregating clinical intake facts.
    Follows Section 20 of docs/API_CONTRACTS.md.
    """
    patient_name = patient_data.get("name", "Patient")
    chief_complaint_text = "No chief complaint recorded"
    hpi_text = "No history of present illness recorded"
    medications: List[str] = []
    investigations: List[str] = []
    relevant_history: List[str] = []
    allergies_text = "No allergy reported"

    if responses:
        for r in responses:
            q_id = r.get("question_id", "")
            ans = r.get("answer_text", "")
            if "CHIEF" in q_id or not chief_complaint_text or chief_complaint_text == "No chief complaint recorded":
                chief_complaint_text = ans
            if "DUR" in q_id or "ONSET" in q_id:
                hpi_text = f"{chief_complaint_text} ({ans})"

    if history_data:
        cc_val = history_data.get("chief_complaint")
        if isinstance(cc_val, dict) and cc_val.get("value"):
            chief_complaint_text = cc_val.get("value")
        elif isinstance(cc_val, str) and cc_val:
            chief_complaint_text = cc_val

        hpi_val = history_data.get("history_of_present_illness")
        if isinstance(hpi_val, dict):
            parts = [f"{k}: {v.get('value') if isinstance(v, dict) else v}" for k, v in hpi_val.items() if v]
            if parts:
                hpi_text = "; ".join(parts)
        elif isinstance(hpi_val, str) and hpi_val:
            hpi_text = hpi_val

        for med in history_data.get("current_medications", []):
            if isinstance(med, dict):
                med_desc = f"{med.get('medicine', '')} {med.get('dosage', '')} {med.get('frequency', '')}".strip()
                if med_desc:
                    medications.append(med_desc)
            elif isinstance(med, str):
                medications.append(med)

        for pmh in history_data.get("past_medical_history", []):
            if isinstance(pmh, str):
                relevant_history.append(pmh)
            elif isinstance(pmh, dict) and pmh.get("value"):
                relevant_history.append(pmh["value"])

    if extracted_docs:
        for doc in extracted_docs:
            for med in doc.get("medications", []):
                med_desc = f"{med.get('medicine', '')} {med.get('dosage', '')} {med.get('frequency', '')}".strip()
                if med_desc and med_desc not in medications:
                    medications.append(med_desc)
            for inv in doc.get("investigations", []):
                if inv not in investigations:
                    investigations.append(inv)

    if timeline_events:
        for ev in timeline_events:
            title = ev.get("title", "")
            date = ev.get("event_date", "")
            if title:
                investigations.append(f"{title} - {date}" if date else title)

    summary_text = (
        f"Patient {patient_name} presents for consultation. "
        f"Chief complaint: {chief_complaint_text}. "
        f"History of Present Illness: {hpi_text}."
    )

    return {
        "summary_text": summary_text,
        "structured_summary": {
            "chief_complaint": chief_complaint_text,
            "history_of_present_illness": hpi_text,
            "relevant_history": relevant_history,
            "current_medications": medications,
            "relevant_investigations": investigations,
            "allergies": allergies_text
        }
    }
