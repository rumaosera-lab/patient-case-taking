// frontend/services/patientApi.ts
//
// Patient-side API layer for MediKiosk.
// Strictly conforms to docs/API_CONTRACTS.md and FastAPI backend endpoints in backend/api/.

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// ---------------------------------------------------------------------------
// Types & Interfaces (Matching API_CONTRACTS.md & FastAPI models)
// ---------------------------------------------------------------------------

export type PreferredLanguageCode = "en" | "hi" | "mr";

export interface PatientRegistrationPayload {
  name: string;
  date_of_birth: string;
  gender: string;
  phone: string;
  preferred_language: PreferredLanguageCode;
  abha_id?: string | null;
}

export interface PatientData {
  patient_id: string;
  name: string;
  date_of_birth: string;
  gender: string;
  phone: string;
  preferred_language: PreferredLanguageCode;
  abha_id: string | null;
  created_at?: string;
  updated_at?: string;
}

export type SessionStatus =
  | "IN_PROGRESS"
  | "PROCESSING"
  | "COMPLETED"
  | "READY_FOR_DOCTOR"
  | "REVIEWED";

export interface SessionCreatePayload {
  patient_id: string;
  department?: string;
}

export interface SessionData {
  session_id: string;
  patient_id: string;
  status: SessionStatus;
  department: string;
  started_at: string;
  completed_at?: string | null;
  last_updated_at?: string;
}

export interface ResponseSubmitPayload {
  question_id: string;
  question_text: string;
  answer_text: string;
  input_type: "voice" | "text" | "touch" | "choice";
  language: PreferredLanguageCode;
}

export interface SubmittedResponseData {
  response_id: string;
  session_id: string;
  question_id: string;
  answer_text: string;
  input_type: string;
  language: string;
  timestamp: string;
}

export interface ClinicalHistoryUpdatePayload {
  chief_complaint?: {
    value: string;
    source?: { type: string; source_id: string };
  };
  history_of_present_illness?: Record<
    string,
    { value: unknown; source?: { type: string; source_id: string } }
  >;
  past_medical_history?: Array<Record<string, unknown>>;
  past_surgical_history?: Array<Record<string, unknown>>;
  current_medications?: Array<Record<string, unknown>>;
  allergies?: Array<Record<string, unknown>>;
  family_history?: Array<Record<string, unknown>>;
  personal_history?: Array<Record<string, unknown>>;
  review_of_systems?: Array<Record<string, unknown>>;
}

export interface CaseSummaryData {
  summary_id: string;
  patient_id: string;
  session_id: string;
  summary_text: string;
  structured_summary: {
    chief_complaint: string;
    history_of_present_illness: string;
    relevant_history: string[];
    current_medications: string[];
    relevant_investigations: string[];
    allergies: string;
  };
  generated_at: string;
  review_status: "GENERATED" | "EDITED" | "APPROVED";
  reviewed_by?: string | null;
  doctor_notes?: string | null;
  approved_at?: string | null;
}

export interface DocumentUploadResponse {
  document_id: string;
  file_name: string;
  document_type: string;
  processing_status: string;
}

// ---------------------------------------------------------------------------
// Standard response envelope (Matching API_CONTRACTS.md Sec 5)
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
    return data as ApiResponse<T>;
  } catch (err) {
    console.warn(`API request to ${path} failed or backend is offline:`, err);
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
// Patient Authentication & Registration APIs
// ---------------------------------------------------------------------------

/**
 * Register a new patient or update existing profile
 * POST /api/v1/patients
 */
export async function registerPatient(
  payload: PatientRegistrationPayload
): Promise<ApiResponse<PatientData>> {
  return apiFetch<PatientData>("/patients", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Retrieve patient by application ID
 * GET /api/v1/patients/{patient_id}
 */
export async function getPatient(
  patientId: string
): Promise<ApiResponse<PatientData>> {
  return apiFetch<PatientData>(`/patients/${patientId}`);
}

/**
 * Check if patient has an active (IN_PROGRESS) session
 * GET /api/v1/patients/{patient_id}/sessions/active
 */
export async function getActivePatientSession(
  patientId: string
): Promise<ApiResponse<{ session_id: string; status: SessionStatus } | null>> {
  return apiFetch<{ session_id: string; status: SessionStatus } | null>(
    `/patients/${patientId}/sessions/active`
  );
}

// ---------------------------------------------------------------------------
// Patient Session Management APIs
// ---------------------------------------------------------------------------

/**
 * Create a new clinical intake session
 * POST /api/v1/sessions
 */
export async function createSession(
  payload: SessionCreatePayload
): Promise<ApiResponse<SessionData>> {
  return apiFetch<SessionData>("/sessions", {
    method: "POST",
    body: JSON.stringify({
      patient_id: payload.patient_id,
      department: payload.department || "General Medicine",
    }),
  });
}

/**
 * Update session status (e.g. mark READY_FOR_DOCTOR upon completion)
 * PATCH /api/v1/sessions/{session_id}
 */
export async function updateSessionStatus(
  sessionId: string,
  status: SessionStatus
): Promise<ApiResponse<SessionData>> {
  return apiFetch<SessionData>(`/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

// ---------------------------------------------------------------------------
// Response & History Submission APIs
// ---------------------------------------------------------------------------

/**
 * Submit an individual question response
 * POST /api/v1/sessions/{session_id}/responses
 */
export async function submitSessionResponse(
  sessionId: string,
  payload: ResponseSubmitPayload
): Promise<ApiResponse<SubmittedResponseData>> {
  return apiFetch<SubmittedResponseData>(`/sessions/${sessionId}/responses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Submit structured clinical history
 * PATCH /api/v1/sessions/{session_id}/history
 */
export async function submitClinicalHistory(
  sessionId: string,
  payload: ClinicalHistoryUpdatePayload
): Promise<ApiResponse<Record<string, unknown>>> {
  return apiFetch<Record<string, unknown>>(`/sessions/${sessionId}/history`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Case Summary APIs
// ---------------------------------------------------------------------------

/**
 * Trigger AI clinical case summary generation
 * POST /api/v1/sessions/{session_id}/summary
 */
export async function generateCaseSummary(
  sessionId: string
): Promise<ApiResponse<CaseSummaryData>> {
  return apiFetch<CaseSummaryData>(`/sessions/${sessionId}/summary`, {
    method: "POST",
  });
}

// ---------------------------------------------------------------------------
// Timeline APIs
// ---------------------------------------------------------------------------

export interface TimelineEventItem {
  event_id: string;
  patient_id: string;
  session_id?: string;
  event_date: string;
  event_type: string;
  title: string;
  description: string;
  source_type: string;
  source_id?: string;
  created_at?: string;
}

export interface PatientTimelineResponse {
  patient_id: string;
  events: TimelineEventItem[];
}

/**
 * Retrieve patient medical timeline events
 * GET /api/v1/patients/{patient_id}/timeline
 */
export async function getPatientTimeline(
  patientId: string
): Promise<ApiResponse<PatientTimelineResponse>> {
  return apiFetch<PatientTimelineResponse>(`/patients/${patientId}/timeline`);
}

// ---------------------------------------------------------------------------
// Document Upload API
// ---------------------------------------------------------------------------

/**
 * Upload a patient medical document (Prescription, Lab Report, etc.)
 * POST /api/v1/sessions/{session_id}/documents
 */
export async function uploadPatientDocument(
  sessionId: string,
  file: File,
  documentType: "prescription" | "lab_report" | "discharge_summary" | "medical_report" | "other" = "medical_report"
): Promise<ApiResponse<DocumentUploadResponse>> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", documentType);

    const res = await fetch(`${BASE_URL}/sessions/${sessionId}/documents`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    return data as ApiResponse<DocumentUploadResponse>;
  } catch (err) {
    console.warn(`Document upload failed:`, err);
    return {
      success: false,
      error: {
        code: "UPLOAD_ERROR",
        message: err instanceof Error ? err.message : "Failed to upload document",
      },
    };
  }
}

