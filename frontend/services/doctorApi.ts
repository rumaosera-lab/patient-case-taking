// services/doctorApi.ts
//
// Doctor-side API layer.
// Every type and endpoint here is taken directly from API_CONTRACTS.md.
// Nothing in this file is invented — anything not explicitly confirmed
// in the contract or by the team is marked with a "CONFIRM" comment.

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// ---------------------------------------------------------------------------
// Types (from API_CONTRACTS.md)
// ---------------------------------------------------------------------------

export interface Patient {
  patient_id: string;
  name: string;
  date_of_birth: string;
  gender: string;
  phone: string;
  preferred_language: "en" | "hi" | "mr";
  abha_id: string | null;
}

export type SessionStatus =
  | "IN_PROGRESS"
  | "PROCESSING"
  | "COMPLETED"
  | "READY_FOR_DOCTOR"
  | "REVIEWED";

export interface Session {
  session_id: string;
  patient_id: string;
  status: SessionStatus;
  department: string;
  started_at: string;
  completed_at: string | null;
  last_updated_at: string;
}

export type ReviewStatus = "GENERATED" | "EDITED" | "APPROVED";

export interface StructuredSummary {
  chief_complaint: string;
  history_of_present_illness: string;
  relevant_history: string[];
  current_medications: string[];
  relevant_investigations: string[];
  allergies: string;
}

export interface CaseSummary {
  summary_id: string;
  patient_id: string;
  session_id: string;
  summary_text: string;
  structured_summary: StructuredSummary;
  generated_at: string;
  reviewed_by: string | null;
  review_status: ReviewStatus;
  doctor_notes: string | null;
  approved_at: string | null;
}

export type EventType =
  | "diagnosis"
  | "medication"
  | "investigation"
  | "procedure"
  | "hospitalization"
  | "surgery"
  | "symptom"
  | "other";

export interface TimelineEvent {
  event_id: string;
  patient_id: string;
  session_id: string;
  event_date: string;
  event_type: EventType;
  title: string;
  description: string;
  source_type: "patient_response" | "document" | "previous_record";
  source_id: string;
  created_at: string;
}

export type DocumentType =
  | "prescription"
  | "lab_report"
  | "discharge_summary"
  | "medical_report"
  | "other";

export type ProcessingStatus = "UPLOADED" | "PROCESSING" | "PROCESSED" | "FAILED";

export interface DocumentObject {
  document_id: string;
  patient_id: string;
  session_id: string;
  file_name: string;
  document_type: DocumentType;
  file_url: string;
  processing_status: ProcessingStatus;
  uploaded_at: string;
}

export interface FieldSource {
  type: "patient_response" | "document" | "previous_record";
  source_id: string;
  page?: number;
}

// CONFIRM: API_CONTRACTS.md Sec 15.1 shows history_of_present_illness as an
// object of named fields (duration, location, ...), each with value+source.
// past_medical_history / medications / allergies / etc. are shown as empty
// arrays with no example item shape given. Left as unknown[] until a real
// populated example or explicit field contract is confirmed by Sera/Bernice.
export interface ClinicalHistory {
  history_id: string;
  session_id: string;
  chief_complaint: { value: string; source: FieldSource };
  history_of_present_illness: Record<
    string,
    { value: string; source: FieldSource }
  >;
  past_medical_history: unknown[];
  past_surgical_history: unknown[];
  current_medications: unknown[];
  allergies: unknown[];
  family_history: unknown[];
  personal_history: unknown[];
  review_of_systems: unknown[];
  created_at: string;
  updated_at: string;
}

// Confirmed by user: this shape (Sec 21.2 example) applies across Section 21
// as a whole — 21.1 (list) returns an array of these, 21.2 (single record)
// returns one directly.
export interface DoctorPatientRecord {
  patient: Patient;
  current_session: Session;
  case_summary: CaseSummary;
  relevant_history: ClinicalHistory;
  timeline: TimelineEvent[];
  documents: DocumentObject[];
}

// ---------------------------------------------------------------------------
// Standard response envelope (API_CONTRACTS.md Sec 5)
// ---------------------------------------------------------------------------

interface ApiSuccess<T> {
  success: true;
  data: T;
  message?: string;
}

interface ApiErrorShape {
  success: false;
  error: { code: string; message: string };
}

export type ApiResponse<T> = ApiSuccess<T> | ApiErrorShape;

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      ...options,
    });

    const data = await res.json();
    if (!res.ok && (!data || !("success" in data))) {
      let msg = res.statusText || "Request failed";
      if (data && data.detail) {
        if (Array.isArray(data.detail)) {
          msg = data.detail
            .map((d: { msg?: string }) => d.msg || JSON.stringify(d))
            .join(", ");
        } else if (typeof data.detail === "string") {
          msg = data.detail;
        }
      }
      return {
        success: false,
        error: {
          code: `HTTP_${res.status}`,
          message: msg,
        },
      };
    }
    return data as ApiResponse<T>;
  } catch (err) {
    console.warn(`Doctor API request to ${path} failed:`, err);
    return {
      success: false,
      error: {
        code: "NETWORK_ERROR",
        message:
          err instanceof Error
            ? err.message
            : "Could not connect to FastAPI backend server",
      },
    };
  }
}

// ---------------------------------------------------------------------------
// Auth — Doctor Login (Sec 12.2)
// ---------------------------------------------------------------------------

export function loginDoctor(email: string, password: string) {
  return apiFetch<{
    access_token: string;
    token_type: string;
    user: { user_id: string; role: "doctor" };
  }>("/auth/doctor/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// ---------------------------------------------------------------------------
// Doctor APIs (Sec 21)
// ---------------------------------------------------------------------------

/**
 * GET /doctors/{doctor_id}/patients
 * Sec 21.1: backend prioritizes/sorts READY_FOR_DOCTOR sessions first.
 * Confirmed by user: returns an array of full DoctorPatientRecord objects
 * (same shape as the single-record endpoint below).
 */
export function getDoctorPatients(doctorId: string) {
  return apiFetch<DoctorPatientRecord[]>(`/doctors/${doctorId}/patients`);
}

/**
 * GET /doctors/{doctor_id}/patients/{patient_id}/record
 * Sec 21.2
 */
export function getDoctorPatientRecord(doctorId: string, patientId: string) {
  return apiFetch<DoctorPatientRecord>(
    `/doctors/${doctorId}/patients/${patientId}/record`
  );
}

// ---------------------------------------------------------------------------
// Doctor Editing (Sec 22)
// ---------------------------------------------------------------------------

/**
 * PATCH /sessions/{session_id}/history
 * Only send the fields being corrected. Per Sec 22, this must not erase
 * the original patient response or document source — the backend is
 * responsible for preserving that; the frontend just sends the correction.
 */
export function updateSessionHistory(
  sessionId: string,
  partialHistory: Record<string, unknown>
) {
  return apiFetch<ClinicalHistory>(`/sessions/${sessionId}/history`, {
    method: "PATCH",
    body: JSON.stringify(partialHistory),
  });
}

// ---------------------------------------------------------------------------
// Doctor Approval (Sec 23)
// ---------------------------------------------------------------------------

export function approveSession(sessionId: string) {
  return apiFetch<{
    session_id: string;
    status: SessionStatus;
    review_status: ReviewStatus;
    reviewed_by: string;
    approved_at: string;
  }>(`/sessions/${sessionId}/approve`, { method: "POST" });
}
