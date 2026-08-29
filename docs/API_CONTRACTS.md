# Patient Case-Taking Software — API & JSON Contracts

## SIH 2026 Internal Round

---

# 1. Purpose

This document defines the communication contracts between the frontend, backend, database, AI services, OCR services, and other application modules.

This file is the **single technical source of truth for API and JSON structures**.

All developers and AI coding tools must follow these contracts.

No module should independently invent alternative request formats, response formats, field names, status values, or data structures without updating this document and obtaining team agreement.

---

# 2. API Architecture

The application follows this communication flow:

```text
Next.js Frontend
       |
       | HTTP / JSON
       ↓
FastAPI Backend
       |
       ├──────────────→ MongoDB Atlas
       |
       ├──────────────→ AI Services
       |
       └──────────────→ OCR / Document Services
```

The frontend must **never directly access MongoDB**.

The frontend communicates with the FastAPI backend.

AI and OCR services are accessed through the backend.

---

# 3. API Base URL

All APIs use the following prefix:

```text
/api/v1
```

Development example:

```text
http://localhost:8000/api/v1
```

The production URL will be configured through environment variables.

The frontend must not hard-code the production backend URL.

---

# 4. HTTP Methods

| Method | Purpose                                     |
| ------ | ------------------------------------------- |
| GET    | Retrieve data                               |
| POST   | Create or submit data                       |
| PATCH  | Partially update data                       |
| PUT    | Full replacement when specifically required |
| DELETE | Delete a resource when explicitly supported |

The MVP will primarily use:

```text
GET
POST
PATCH
```

Unnecessary DELETE or PUT endpoints should not be added without a clear requirement.

---

# 5. Standard API Response Format

All JSON API responses must follow a consistent structure.

## Successful response

```json
{
  "success": true,
  "data": {},
  "message": "Operation successful"
}
```

`message` is optional when the returned data is self-explanatory.

Example:

```json
{
  "success": true,
  "data": {
    "patient_id": "PAT-000001",
    "name": "Rahul Sharma"
  },
  "message": "Patient registered successfully"
}
```

## Error response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

The backend should not expose internal stack traces, database errors, API keys, or other sensitive implementation details to the frontend.

---

# 6. Standard Error Codes

The following error codes are available:

```text
VALIDATION_ERROR
INVALID_REQUEST
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
DUPLICATE_RESOURCE
SESSION_NOT_FOUND
PATIENT_NOT_FOUND
DOCTOR_NOT_FOUND
DOCUMENT_NOT_FOUND
SUMMARY_NOT_FOUND
PROCESSING_ERROR
DATABASE_ERROR
AI_ERROR
OCR_ERROR
INTERNAL_SERVER_ERROR
```

Resource-specific errors may be added when they provide meaningful information.

---

# 7. ID Convention

The application uses human-readable application IDs.

Examples:

```text
PAT-000001
DOC-000001
SES-000001
RESP-000001
HIS-000001
EXT-000001
EVT-000001
SUM-000001
```

MongoDB's internal `_id` may still exist.

Application APIs should primarily use the application-level IDs.

---

# 8. Date and Time Convention

Dates without time use:

```text
YYYY-MM-DD
```

Example:

```text
2026-08-29
```

Timestamps use ISO 8601.

Example:

```text
2026-08-29T09:30:00Z
```

All stored timestamps should be normalized consistently.

---

# 9. Language Convention

Supported language codes:

| Code | Language |
| ---- | -------- |
| `en` | English  |
| `hi` | Hindi    |
| `mr` | Marathi  |

Hinglish may be accepted as natural-language input but does not require a separate language code for the MVP.

---

# 10. Patient API

## 10.1 Create Patient

```http
POST /api/v1/patients
```

### Request

```json
{
  "name": "Rahul Sharma",
  "date_of_birth": "1981-04-12",
  "gender": "Male",
  "phone": "9876543210",
  "preferred_language": "hi"
}
```

### Required fields

```text
name
date_of_birth
gender
phone
preferred_language
```

### Optional fields

```text
abha_id
```

### Response

```json
{
  "success": true,
  "data": {
    "patient_id": "PAT-000001",
    "name": "Rahul Sharma",
    "preferred_language": "hi"
  },
  "message": "Patient registered successfully"
}
```

---

## 10.2 Get Patient

```http
GET /api/v1/patients/{patient_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "patient_id": "PAT-000001",
    "name": "Rahul Sharma",
    "date_of_birth": "1981-04-12",
    "gender": "Male",
    "phone": "9876543210",
    "preferred_language": "hi",
    "abha_id": null
  }
}
```

---

## 10.3 Update Patient

```http
PATCH /api/v1/patients/{patient_id}
```

Only supplied fields should be updated.

### Request

```json
{
  "phone": "9876543211",
  "preferred_language": "mr"
}
```

---

# 11. Doctor API

## 11.1 Doctor Object

```json
{
  "doctor_id": "DOC-000001",
  "name": "Dr. Mehta",
  "email": "doctor@example.com",
  "department": "General Medicine",
  "created_at": "2026-08-29T09:00:00Z",
  "updated_at": "2026-08-29T09:00:00Z"
}
```

`password_hash` is a database-only field.

It must never be returned through an API response.

---

# 12. Authentication API

Authentication implementation belongs to Phase 10, but the API contract is reserved here.

## 12.1 Patient Login

```http
POST /api/v1/auth/patient/login
```

### Request

```json
{
  "phone": "9876543210",
  "password": "..."
}
```

### Response

```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "token_type": "bearer",
    "user": {
      "user_id": "PAT-000001",
      "role": "patient"
    }
  }
}
```

---

## 12.2 Doctor Login

```http
POST /api/v1/auth/doctor/login
```

### Request

```json
{
  "email": "doctor@example.com",
  "password": "..."
}
```

### Response

```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "token_type": "bearer",
    "user": {
      "user_id": "DOC-000001",
      "role": "doctor"
    }
  }
}
```

JWT implementation and protected routes are handled in Phase 10.

---

# 13. Session API

A session represents one patient interaction or visit.

## 13.1 Session Object

```json
{
  "session_id": "SES-000001",
  "patient_id": "PAT-000001",
  "status": "IN_PROGRESS",
  "department": "General Medicine",
  "started_at": "2026-08-29T09:30:00Z",
  "completed_at": null,
  "last_updated_at": "2026-08-29T09:45:00Z"
}
```

## 13.2 Session Status

Only the following statuses are valid:

```text
IN_PROGRESS
PROCESSING
COMPLETED
READY_FOR_DOCTOR
REVIEWED
```

Invalid values must be rejected by backend validation.

---

## 13.3 Create Session

```http
POST /api/v1/sessions
```

### Request

```json
{
  "patient_id": "PAT-000001",
  "department": "General Medicine"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "session_id": "SES-000001",
    "patient_id": "PAT-000001",
    "status": "IN_PROGRESS",
    "department": "General Medicine",
    "started_at": "2026-08-29T09:30:00Z"
  }
}
```

---

## 13.4 Get Session

```http
GET /api/v1/sessions/{session_id}
```

---

## 13.5 Update Session

```http
PATCH /api/v1/sessions/{session_id}
```

### Request

```json
{
  "status": "PROCESSING"
}
```

The backend must validate allowed status transitions.

---

## 13.6 Find Active Session

```http
GET /api/v1/patients/{patient_id}/sessions/active
```

### Active session response

```json
{
  "success": true,
  "data": {
    "session_id": "SES-000001",
    "status": "IN_PROGRESS",
    "last_updated_at": "2026-08-29T09:45:00Z"
  }
}
```

### No active session

```json
{
  "success": true,
  "data": null,
  "message": "No active session found"
}
```

This endpoint supports session resumption.

---

# 14. Response API

The response collection stores the patient's actual answer.

The raw answer and AI interpretation must remain conceptually separate.

## 14.1 Response Object

```json
{
  "response_id": "RESP-000001",
  "session_id": "SES-000001",
  "question_id": "Q-CHEST-001",
  "question_text": "What is your main problem today?",
  "answer_text": "Mujhe do din se chest mein pain hai.",
  "input_type": "voice",
  "language": "hi",
  "timestamp": "2026-08-29T09:50:00Z"
}
```

## 14.2 Input Types

```text
voice
text
touch
```

## 14.3 Submit Response

```http
POST /api/v1/sessions/{session_id}/responses
```

### Request

```json
{
  "question_id": "Q-CHEST-001",
  "question_text": "What is your main problem today?",
  "answer_text": "Mujhe do din se chest mein pain hai.",
  "input_type": "voice",
  "language": "hi"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "response_id": "RESP-000001",
    "session_id": "SES-000001",
    "question_id": "Q-CHEST-001",
    "answer_text": "Mujhe do din se chest mein pain hai.",
    "input_type": "voice",
    "language": "hi",
    "timestamp": "2026-08-29T09:50:00Z"
  }
}
```

---

## 14.4 Get Responses

```http
GET /api/v1/sessions/{session_id}/responses
```

Returns the patient's recorded responses in chronological order.

---

# 15. Clinical History API

The structured clinical history is derived from patient responses and other approved information sources.

It must remain separate from raw patient responses.

## 15.1 Clinical History Object

```json
{
  "history_id": "HIS-000001",
  "session_id": "SES-000001",
  "chief_complaint": {
    "value": "chest pain",
    "source": {
      "type": "patient_response",
      "source_id": "RESP-000001"
    }
  },
  "history_of_present_illness": {
    "duration": {
      "value": "2 days",
      "source": {
        "type": "patient_response",
        "source_id": "RESP-000001"
      }
    },
    "location": {
      "value": "central chest",
      "source": {
        "type": "patient_response",
        "source_id": "RESP-000003"
      }
    }
  },
  "past_medical_history": [],
  "past_surgical_history": [],
  "current_medications": [],
  "allergies": [],
  "family_history": [],
  "personal_history": [],
  "review_of_systems": [],
  "created_at": "2026-08-29T10:00:00Z",
  "updated_at": "2026-08-29T10:00:00Z"
}
```

---

## 15.2 Get Clinical History

```http
GET /api/v1/sessions/{session_id}/history
```

---

## 15.3 Update Clinical History

```http
PATCH /api/v1/sessions/{session_id}/history
```

This endpoint may later be used by authorized doctors to correct information.

---

# 16. Source Contract

Important extracted information should retain its source.

## Patient response source

```json
{
  "type": "patient_response",
  "source_id": "RESP-000001"
}
```

## Document source

```json
{
  "type": "document",
  "source_id": "DOC-000001",
  "page": 1
}
```

## Previous record source

```json
{
  "type": "previous_record",
  "source_id": "..."
}
```

Allowed source types:

```text
patient_response
document
previous_record
```

Source information should be retained whenever technically possible.

---

# 17. Document API

Documents contain uploaded medical files.

## 17.1 Document Object

```json
{
  "document_id": "DOC-000001",
  "patient_id": "PAT-000001",
  "session_id": "SES-000001",
  "file_name": "prescription.pdf",
  "document_type": "prescription",
  "file_url": "...",
  "processing_status": "UPLOADED",
  "uploaded_at": "2026-08-29T10:05:00Z"
}
```

## 17.2 Document Types

```text
prescription
lab_report
discharge_summary
medical_report
other
```

## 17.3 Processing Status

```text
UPLOADED
PROCESSING
PROCESSED
FAILED
```

---

## 17.4 Upload Document

```http
POST /api/v1/sessions/{session_id}/documents
```

Content type:

```text
multipart/form-data
```

Example conceptual request:

```text
file = prescription.pdf
document_type = prescription
```

### Response

```json
{
  "success": true,
  "data": {
    "document_id": "DOC-000001",
    "file_name": "prescription.pdf",
    "document_type": "prescription",
    "processing_status": "UPLOADED"
  }
}
```

---

## 17.5 Get Document

```http
GET /api/v1/documents/{document_id}
```

---

## 17.6 Get Extraction

```http
GET /api/v1/documents/{document_id}/extraction
```

---

# 18. Medical Extraction Contract

Medical information extracted from a document must follow a structured format.

## Example

```json
{
  "extraction_id": "EXT-000001",
  "document_id": "DOC-000001",
  "patient_id": "PAT-000001",
  "diagnoses": [],
  "medications": [
    {
      "medicine": "Amlodipine",
      "dosage": "5 mg",
      "frequency": "once daily",
      "source": {
        "type": "document",
        "source_id": "DOC-000001",
        "page": 1
      }
    }
  ],
  "investigations": [],
  "procedures": [],
  "extracted_text": "...",
  "confidence": 0.94,
  "created_at": "2026-08-29T10:10:00Z"
}
```

If information is not present, use an empty array.

Example:

```json
"diagnoses": []
```

The system must never invent medical information to fill missing fields.

---

# 19. Timeline API

## 19.1 Timeline Event

```json
{
  "event_id": "EVT-000001",
  "patient_id": "PAT-000001",
  "session_id": "SES-000001",
  "event_date": "2026-06-15",
  "event_type": "investigation",
  "title": "ECG",
  "description": "ECG recorded in uploaded medical report.",
  "source_type": "document",
  "source_id": "DOC-000004",
  "created_at": "2026-08-29T10:15:00Z"
}
```

## 19.2 Event Types

Initial event types:

```text
diagnosis
medication
investigation
procedure
hospitalization
surgery
symptom
other
```

Additional event types may be added later if required.

---

## 19.3 Get Patient Timeline

```http
GET /api/v1/patients/{patient_id}/timeline
```

### Response

```json
{
  "success": true,
  "data": {
    "patient_id": "PAT-000001",
    "events": []
  }
}
```

Events should be returned in chronological order.

---

# 20. Case Summary API

## 20.1 Summary Object

```json
{
  "summary_id": "SUM-000001",
  "patient_id": "PAT-000001",
  "session_id": "SES-000001",
  "summary_text": "Patient reports intermittent central chest pain for 2 days.",
  "structured_summary": {
    "chief_complaint": "Chest pain - 2 days",
    "history_of_present_illness": "Central intermittent chest pain.",
    "relevant_history": [
      "Hypertension",
      "Diabetes"
    ],
    "current_medications": [
      "Amlodipine 5 mg"
    ],
    "relevant_investigations": [
      "ECG - 2026-06-15"
    ],
    "allergies": "No allergy reported"
  },
  "generated_at": "2026-08-29T10:20:00Z",
  "reviewed_by": null,
  "review_status": "GENERATED",
  "doctor_notes": null,
  "approved_at": null
}
```

## 20.2 Review Status

```text
GENERATED
EDITED
APPROVED
```

The AI-generated summary is a draft until reviewed and approved by a doctor.

---

## 20.3 Generate Summary

```http
POST /api/v1/sessions/{session_id}/summary
```

The backend will eventually call the summarization service.

---

## 20.4 Get Summary

```http
GET /api/v1/sessions/{session_id}/summary
```

---

# 21. Doctor APIs

## 21.1 Get Patient List

```http
GET /api/v1/doctors/{doctor_id}/patients
```

The endpoint should prioritize patients/sessions that are:

```text
READY_FOR_DOCTOR
```

Filtering can be added later.

---

## 21.2 Get Complete Patient Record

```http
GET /api/v1/doctors/{doctor_id}/patients/{patient_id}/record
```

The response should be doctor-oriented.

Example:

```json
{
  "success": true,
  "data": {
    "patient": {},
    "current_session": {},
    "case_summary": {},
    "relevant_history": {},
    "timeline": [],
    "documents": []
  }
}
```

The API should combine information from the underlying collections instead of exposing the raw database structure directly.

---

# 22. Doctor Editing

```http
PATCH /api/v1/sessions/{session_id}/history
```

The doctor may correct incorrect structured information.

Example:

```json
{
  "current_medications": [
    {
      "medicine": "Amlodipine",
      "dosage": "5 mg",
      "frequency": "once daily"
    }
  ]
}
```

Doctor modifications should not erase the original patient response or document source.

---

# 23. Doctor Approval

```http
POST /api/v1/sessions/{session_id}/approve
```

### Response

```json
{
  "success": true,
  "data": {
    "session_id": "SES-000001",
    "status": "REVIEWED",
    "review_status": "APPROVED",
    "reviewed_by": "DOC-000001",
    "approved_at": "2026-08-29T11:00:00Z"
  },
  "message": "Patient record approved successfully"
}
```

---

# 24. Clinical Question Contract

The clinical question engine controls what information needs to be collected.

The LLM must not independently control the entire interview.

## Question Object

```json
{
  "question_id": "Q-CHEST-003",
  "field": "location",
  "question_text": "Where exactly do you feel the pain?",
  "input_type": "text",
  "required": true,
  "options": null
}
```

For a yes/no question:

```json
{
  "question_id": "Q-CHEST-004",
  "field": "radiation",
  "question_text": "Does the pain move to another part of your body?",
  "input_type": "yes_no",
  "required": true,
  "options": null
}
```

The clinical framework determines which information is required.

The AI helps understand natural-language answers.

---

# 25. AI Information-Extraction Contract

Gemini must receive controlled inputs.

## Input

```json
{
  "question_id": "Q-CHEST-002",
  "question": "How long have you had the pain?",
  "patient_answer": "Mujhe do din se ho raha hai.",
  "language": "hi",
  "expected_fields": [
    "duration"
  ]
}
```

## Output

```json
{
  "extracted_fields": {
    "duration": "2 days"
  },
  "unmentioned_fields": [],
  "confidence": 0.95
}
```

The backend must validate AI output before using it.

---

# 26. AI Safety Rules

The AI may:

```text
Extract information
Normalize information
Understand natural language
Interpret multilingual responses
Structure information
```

The AI must not:

```text
Diagnose the patient
Invent symptoms
Invent medications
Invent dates
Invent medical history
Make autonomous clinical decisions
Determine emergency status
Replace the doctor
```

If information is not present, the AI should leave the relevant field empty or identify it as unmentioned.

---

# 27. AI Data Flow

```text
Patient Answer
      ↓
AI Extraction
      ↓
Structured JSON
      ↓
Backend Validation
      ↓
Clinical History
      ↓
MongoDB
```

The AI must never directly write to MongoDB.

The backend remains responsible for validation and persistence.

---

# 28. OCR Contract

The OCR/document pipeline follows:

```text
Uploaded Document
       ↓
File Processing
       ↓
OCR / Vision
       ↓
Extracted Text
       ↓
Medical Information Extraction
       ↓
Structured JSON
       ↓
MongoDB
```

## OCR Output

```json
{
  "document_id": "DOC-000001",
  "extracted_text": "Tab Amlodipine 5 mg once daily...",
  "pages": [
    {
      "page": 1,
      "text": "Tab Amlodipine 5 mg once daily..."
    }
  ]
}
```

OCR should preserve page information when possible because source traceability may require document-page references.

---

# 29. Validation Rules

The backend must validate:

### Required fields

Required fields cannot be missing.

### Data types

Examples:

```text
patient_id → string
date_of_birth → date
confidence → number
required → boolean
```

### Enum values

Fields such as:

```text
session.status
document.document_type
document.processing_status
response.input_type
summary.review_status
source.type
```

must only accept defined values.

### IDs

Referenced IDs must correspond to existing resources where required.

Example:

A response cannot be created for a non-existent session.

### Dates

Dates must follow the agreed date format.

### Empty values

Use:

```json
null
```

when a single optional value is unavailable.

Use:

```json
[]
```

for empty collections.

Do not use inconsistent representations such as:

```text
"None"
"N/A"
"unknown"
""
```

unless explicitly defined by a field contract.

---

# 30. API Endpoint Map

The complete Phase 2 API surface is:

```text
/api/v1

AUTH
├── POST /auth/patient/login
└── POST /auth/doctor/login

PATIENTS
├── POST /patients
├── GET /patients/{patient_id}
├── PATCH /patients/{patient_id}
└── GET /patients/{patient_id}/sessions/active

SESSIONS
├── POST /sessions
├── GET /sessions/{session_id}
└── PATCH /sessions/{session_id}

RESPONSES
├── POST /sessions/{session_id}/responses
└── GET /sessions/{session_id}/responses

HISTORY
├── GET /sessions/{session_id}/history
└── PATCH /sessions/{session_id}/history

DOCUMENTS
├── POST /sessions/{session_id}/documents
├── GET /documents/{document_id}
└── GET /documents/{document_id}/extraction

TIMELINE
└── GET /patients/{patient_id}/timeline

SUMMARY
├── POST /sessions/{session_id}/summary
└── GET /sessions/{session_id}/summary

DOCTORS
├── GET /doctors/{doctor_id}/patients
└── GET /doctors/{doctor_id}/patients/{patient_id}/record

APPROVAL
└── POST /sessions/{session_id}/approve
```

---

# 31. Backend Responsibility

The backend is responsible for:

```text
Request validation
Authentication/authorization
Business rules
AI output validation
OCR output validation
Database operations
Error handling
Source linking
Session state management
```

The backend must not blindly trust data received from the frontend or AI services.

---

# 32. Frontend Responsibility

The frontend is responsible for:

```text
User interaction
Displaying questions
Collecting patient responses
Uploading documents
Displaying processing status
Displaying errors
Displaying patient/doctor records
Calling API endpoints
Following the defined JSON contracts
```

The frontend must not implement its own independent data structures that conflict with the backend contracts.

---

# 33. MongoDB Responsibility

MongoDB Atlas is the persistence layer.

The main collections are:

```text
patients
doctors
sessions
clinical_histories
responses
documents
extracted_information
timeline_events
case_summaries
```

The frontend must not directly access MongoDB.

All database operations must pass through the backend.

---

# 34. Contract Change Rule

No developer or AI coding tool may independently change:

```text
API endpoint names
JSON field names
Status values
Collection relationships
AI output structures
OCR output structures
```

If a change is necessary:

```text
Identify problem
      ↓
Discuss with team
      ↓
Update API_CONTRACTS.md
      ↓
Update affected code
      ↓
Test affected modules
```

The contract must be updated before dependent modules are changed.

---

# 35. Current Contract Status

Phase 2 contract design status:

```text
API structure              → DEFINED
JSON response format       → DEFINED
Patient contracts          → DEFINED
Session contracts          → DEFINED
Response contracts         → DEFINED
History contracts          → DEFINED
Document contracts         → DEFINED
Extraction contracts       → DEFINED
Timeline contracts         → DEFINED
Summary contracts          → DEFINED
Doctor contracts           → DEFINED
AI contracts               → DEFINED
OCR contracts              → DEFINED
Validation rules           → DEFINED
Authentication structure   → RESERVED
Implementation             → PENDING
```

This document defines the contract.

Actual implementation and testing are the next step in Phase 2.
