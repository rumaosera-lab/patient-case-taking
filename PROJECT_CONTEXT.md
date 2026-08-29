# Patient Case-Taking Software — Project Context

## SIH 2026 Internal Round

---

# 1. Project Overview

## Problem Statement

**Patient Case-Taking Software**

## Project Goal

Build an AI-powered pre-consultation clinical intake platform for hospitals.

The system allows a patient to complete their clinical history before meeting the doctor, using voice or text/touch interaction, and upload previous medical documents. The system structures the collected information, extracts relevant information from documents, creates a patient timeline, and generates a concise case summary for the doctor.

The doctor can later log in independently and view the patient's saved record before or during the consultation.

## Core Purpose

The system is focused on:

- Clinical history collection
- Medical information organization
- Medical document digitization
- Pre-consultation preparation
- Reducing repetitive history-taking/document-review workload

The system is **NOT intended to diagnose patients or make autonomous clinical decisions.**

---

# 2. Final MVP Features

## Core Features

1. Patient registration
2. Patient/doctor authentication
3. Language selection
4. Voice-based history taking
5. Text/touch-based alternative
6. Adaptive questioning
7. Medical document upload
8. OCR
9. Medical information extraction
10. Patient timeline
11. AI-generated case summary
12. Doctor dashboard
13. Doctor editing/approval

## Good-to-Have Features

14. Hindi + English + Marathi
15. Text-to-speech
16. Audio instructions

## Removed Feature

### Red-flag detection

Red-flag/urgent symptom detection was removed from the MVP because it moves the application toward triage/diagnosis rather than focusing on the stated problem of clinical history-taking and documentation.

---

# 3. Important Product Decision

The system should NOT simply summarize what the patient would say to the doctor.

The main value is collecting and organizing information that would otherwise require additional history-taking and document review.

Examples:

- Previous illnesses
- Previous surgeries
- Current medications
- Allergies
- Relevant family/personal history
- Previous investigations
- Information from old prescriptions and reports
- Chronological medical events

The system should filter and organize information so that the doctor does not have to read the patient's entire history.

---

# 4. Patient and Doctor Workflow

The patient and doctor workflows are **independent**.

The doctor does NOT have to wait for the patient to finish the process.

## Patient Workflow

```text
Patient Registration
        ↓
Authentication
        ↓
Language Selection
        ↓
Clinical History Taking
        ↓
Voice OR Text/Touch
        ↓
Adaptive Questioning
        ↓
Medical Document Upload
        ↓
OCR
        ↓
Medical Information Extraction
        ↓
Patient Timeline
        ↓
AI Case Summary
        ↓
Save Everything
        ↓
Record Status = READY_FOR_DOCTOR
Break Point

The database is the main break point between patient and doctor workflows.

PATIENT SIDE

Patient
   ↓
AI Processing
   ↓
Database
   ↓
Saved Patient Record
   ↓
DOCTOR SIDE
   ↓
Doctor Login
   ↓
Doctor Dashboard
   ↓
Patient Record

The patient can complete the process hours before the consultation.

The doctor can access the saved record whenever required.

5. Session and Record Status

Each patient interaction/session has a status.

IN_PROGRESS
      ↓
PROCESSING
      ↓
COMPLETED
      ↓
READY_FOR_DOCTOR
      ↓
REVIEWED

If a patient leaves before completion, their progress should be saved rather than lost.

The patient can later resume the same session where applicable.

6. Recommended Tech Stack
Frontend
Next.js
React
Tailwind CSS
TypeScript
Backend
Python
FastAPI

Python is preferred because AI, OCR, document processing, and data-processing libraries integrate well with Python.

Database
MongoDB Atlas

MongoDB is suitable for storing flexible clinical-history structures, extracted document information, sessions, timelines, and summaries.

AI / LLM

Primary option:

Google Gemini API

Use Gemini for:

Understanding natural-language patient responses
Structured information extraction
Medical document understanding
Case-summary generation
Multilingual understanding

The LLM should NOT be allowed to freely determine the entire clinical interview.

Speech-to-Text

Possible options:

Bhashini
Gemini audio capabilities

Final choice should be based on Indian-language support, accuracy, cost, and ease of integration.

Text-to-Speech

Possible options:

Bhashini
Google Cloud Text-to-Speech
OCR

Primary option:

Gemini Vision/document understanding

Possible fallback:

PaddleOCR
Authentication
JWT-based authentication
Password hashing such as bcrypt/passlib where appropriate
Deployment
Frontend → Vercel
Backend → Render
Database → MongoDB Atlas
7. High-Level Architecture
                         ┌─────────────────────┐
                         │      PATIENT        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Next.js Patient UI │
                         └──────────┬──────────┘
                                    │
                       ┌────────────┴────────────┐
                       │                         │
                       ▼                         ▼
                Voice Input              Text / Touch Input
                       │                         │
                       └────────────┬────────────┘
                                    ▼
                              FastAPI Backend
                                    │
                                    ▼
                         Clinical Question Engine
                                    │
                                    ▼
                           Patient Responses
                                    │
                  ┌─────────────────┴─────────────────┐
                  │                                   │
                  ▼                                   ▼
          History Structuring                    Documents
                  │                                   │
                  │                                   ▼
                  │                                  OCR
                  │                                   │
                  │                                   ▼
                  │                       Medical Information Extraction
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
                            Relevant Information
                                    │
                                    ▼
                             Patient Timeline
                                    │
                                    ▼
                             AI Case Summary
                                    │
                                    ▼
                                MongoDB
                                    │
                         ───── BREAK POINT ─────
                                    │
                                    ▼
                           Doctor Authentication
                                    │
                                    ▼
                            Doctor Dashboard
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
                Case Summary                 Full Patient Record
                     │                             │
                     └──────────────┬──────────────┘
                                    ▼
                          Doctor Edit / Approval
8. Clinical Question Architecture

The system should NOT allow an LLM to freely invent medical questions.

Use a structured clinical question framework.

Example:

Complaint: Chest Pain

        ↓
Onset
        ↓
Duration
        ↓
Location
        ↓
Character
        ↓
Radiation
        ↓
Aggravating Factors
        ↓
Relieving Factors
        ↓
Associated Symptoms

The clinical framework determines WHAT information must be collected.

AI determines HOW to understand the patient's natural-language answer and can help phrase questions naturally.

This makes the system more predictable and easier to evaluate.

9. Voice History-Taking Flow

Example:

Patient says:

"Mujhe do din se chest mein pain hai."

Speech-to-text:

Mujhe do din se chest mein pain hai.

AI extraction:

{
  "chiefComplaint": "chest pain",
  "duration": "2 days"
}

The clinical framework checks which required information is still missing.

Next question:

"Where exactly do you feel the pain?"

The process continues until the required history fields are sufficiently covered.

10. Text/Touch Alternative

Every voice question should have a text/touch alternative.

Possible interaction types:

Text input
Multiple-choice buttons
Yes/No buttons
Sliders where appropriate
Simple selectable options

This is important for:

Elderly patients
Low-literacy users
Patients uncomfortable with voice input
Noisy hospital environments
11. Medical Document Pipeline
Upload document
      ↓
Image/PDF processing
      ↓
OCR / Vision
      ↓
Extract text
      ↓
Medical information extraction
      ↓
Structured JSON
      ↓
Store in database
      ↓
Add events to patient timeline

Example:

Uploaded prescription:

Tab Metformin 500 mg
twice daily

Structured output:

{
  "type": "medication",
  "medicine": "Metformin",
  "dosage": "500 mg",
  "frequency": "twice daily"
}

The system must not invent information that is not present in the document.

12. Patient Timeline

Extracted information should be organized chronologically.

Example:

2024
│
├── Hypertension diagnosed
│
2025
│
├── Diabetes recorded
│
2026-06-15
│
├── Blood investigation
│
2026-08-20
│
└── Current prescription

The timeline should be generated from dates found in uploaded documents and patient-provided information.

13. Relevant Information Filtering

The doctor should NOT automatically receive the patient's entire medical history on the main dashboard.

The system should identify information relevant to the current consultation.

Example:

Current complaint:

Chest pain

Relevant information:

Hypertension
Diabetes
Current cardiovascular medication
Previous cardiac investigations
Relevant family history
Relevant previous reports

Unrelated information can remain available under the full history but should not dominate the main dashboard.

14. AI Case Summary

The case summary should be concise and structured.

Example:

CHIEF COMPLAINT
Chest pain – 2 days

HPI
Central intermittent chest pain.
Worsens with exertion.

RELEVANT HISTORY
Hypertension – 2024
Diabetes – 2025

CURRENT MEDICATIONS
Amlodipine 5 mg

RELEVANT INVESTIGATIONS
Previous ECG – 15/06/2026

ALLERGIES
No allergy reported

The summary is a documentation/organization tool, not a diagnosis.

15. Source-Linked Information

This is one of the main technical differentiators.

Every important extracted fact should retain its source.

Example:

{
  "medication": "Amlodipine 5 mg",
  "source": {
    "type": "document",
    "documentId": "DOC_023",
    "page": 1
  }
}

Patient-response example:

{
  "duration": "3 days",
  "source": {
    "type": "patient_response",
    "responseId": "RESP_017"
  }
}

The doctor can click the source and see where the information came from.

Possible source types:

Patient response
Uploaded document
Previous record

This improves transparency and reduces the problem of treating AI output as an unexplained black box.

16. Doctor Dashboard

The doctor dashboard should prioritize relevant information.

Example:

Patient: Rahul Sharma
Age: 45

Today's Complaint
Chest pain – 2 days

Relevant History
Hypertension
Diabetes

Current Medications
Amlodipine 5 mg

Relevant Investigations
Previous ECG – 15/06/2026

Allergies
No allergy reported

[View Full History]
[View Documents]
[Edit]
[Approve]

The doctor should be able to:

View summary
View full history
View original documents
Edit incorrect information
Approve/finalize the case record

The doctor should NOT be forced to verify every AI-generated statement individually.

17. Final Database Architecture

The application uses MongoDB with the following main collections:

patients
doctors
sessions
clinical_histories
responses
documents
extracted_information
timeline_events
case_summaries
17.1 Collection Relationships
                         ┌──────────────┐
                         │   DOCTORS    │
                         └──────┬───────┘
                                │
                                │ reviewed_by
                                ↓
┌──────────────┐         ┌──────────────┐
│   PATIENTS   │────────→│   SESSIONS   │
└──────┬───────┘         └──────┬───────┘
       │                        │
       │                        ├──────────→ RESPONSES
       │                        │
       │                        ├──────────→ CLINICAL_HISTORIES
       │                        │
       │                        ├──────────→ DOCUMENTS
       │                        │                 │
       │                        │                 ↓
       │                        │        EXTRACTED_INFORMATION
       │                        │
       │                        ├──────────→ TIMELINE_EVENTS
       │                        │
       │                        └──────────→ CASE_SUMMARIES
       │
       └──────────────────────────────→ TIMELINE_EVENTS
17.2 patients

Represents the person.

Fields:

patient_id
name
date_of_birth
gender
phone
preferred_language
abha_id
created_at
updated_at

patient_id is the application's internal identifier.

ABHA is optional for the prototype.

Age should preferably be calculated from date of birth rather than permanently stored.

17.3 doctors

Represents doctors who can access patient records.

Fields:

doctor_id
name
email
password_hash
department
created_at
updated_at

The MVP does not require complex hospital role management.

17.4 sessions

Represents an individual patient interaction/visit.

Fields:

session_id
patient_id
status
department
started_at
completed_at
last_updated_at

Example:

{
  "session_id": "SES-000001",
  "patient_id": "PAT-000001",
  "status": "READY_FOR_DOCTOR",
  "department": "General Medicine",
  "started_at": "...",
  "completed_at": "...",
  "last_updated_at": "..."
}

A patient can have multiple sessions.

17.5 responses

Stores the patient's actual answers.

Fields:

response_id
session_id
question_id
question_text
answer_text
input_type
language
timestamp

Possible input types:

voice
text
touch

Raw voice recordings should not be stored unnecessarily for the MVP.

Voice should generally follow:

Voice
 ↓
Speech-to-text
 ↓
answer_text
 ↓
MongoDB
17.6 clinical_histories

Stores the structured clinical history derived from patient responses.

Fields:

history_id
session_id
chief_complaint
history_of_present_illness
past_medical_history
past_surgical_history
current_medications
allergies
family_history
personal_history
review_of_systems
created_at
updated_at

The raw patient response and the structured clinical history should remain separate.

17.7 documents

Stores metadata and references for uploaded medical documents.

Fields:

document_id
patient_id
session_id
file_name
document_type
file_url
processing_status
uploaded_at

Possible document types:

prescription
lab_report
discharge_summary
medical_report
other

Possible processing statuses:

UPLOADED
PROCESSING
PROCESSED
FAILED

The actual image/PDF should preferably be stored in file/object storage rather than directly inside MongoDB.

17.8 extracted_information

Stores medical information extracted from documents.

Fields:

extraction_id
document_id
patient_id
diagnoses
medications
investigations
procedures
extracted_text
confidence
created_at

The extracted information should retain source references where possible.

17.9 timeline_events

Stores chronological medical events.

Fields:

event_id
patient_id
session_id
event_date
event_type
title
description
source_type
source_id
created_at

The source_type and source_id provide traceability.

17.10 case_summaries

Stores AI-generated physician-facing summaries.

Fields:

summary_id
patient_id
session_id
summary_text
structured_summary
generated_at
reviewed_by
review_status
doctor_notes
approved_at

Possible review statuses:

GENERATED
EDITED
APPROVED

The AI-generated summary remains a draft until reviewed/approved by the doctor.

18. Privacy and Data Handling

For the prototype:

Do not store raw voice recordings unnecessarily.
Store structured information after processing.
Delete temporary processing files where appropriate.
Keep uploaded documents protected.
Use environment variables for API keys.
Do not hard-code secrets.
Separate authentication data from clinical data where practical.
Use role-based access for patient and doctor accounts.

The final production system would require proper legal, hospital, consent, security, and health-data compliance review.

19. Differentiation Strategy

The project should NOT become feature-heavy.

Instead, stand out through the quality of implementation.

Differentiator 1 — Clinical History Dataset

Create a structured synthetic dataset containing:

Common complaints
Required history fields
Follow-up questions
Example patient responses
Expected structured outputs

Potential target:

100–300 synthetic clinical cases

Examples:

Fever
Cough
Chest pain
Abdominal pain
Headache
Back pain
Diabetes
Hypertension
20. Specialized Information-Extraction Model

Do NOT train a complete LLM.

Instead, after the baseline system works, consider training a small specialized model for:

Patient response
        ↓
Clinical information fields

Example:

"Mereko kal raat se pet ke right side mein dard hai."

        ↓

symptom = abdominal pain
duration = since last night
location = right abdomen

First build a baseline using Gemini.

Then train/test a smaller specialized model and compare the results.

This provides an actual ML component without attempting to train a large language model from scratch.

The specialized model is optional and should only be attempted after the core application works.

21. Multilingual / Hinglish Testing

The system should eventually be tested with:

English
Hindi
Marathi
Hinglish

Example:

"Mereko 3 din se fever hai."

Expected:

symptom = fever
duration = 3 days

This is particularly relevant to the Indian healthcare context.

22. Medical Document Benchmark

Create a controlled test set of sample/synthetic:

Prescriptions
Blood reports
Discharge summaries

Include variation such as:

Printed documents
Different layouts
Poor image quality
Handwritten samples where feasible
English/Hindi content

Measure:

OCR accuracy
Medical entity extraction accuracy
Date extraction accuracy
Medication extraction accuracy

Only report measured results.

23. Evaluation Strategy

Create a test set and measure the system.

History Collection
Required-field completion rate
Question completeness
Information Extraction
Precision
Recall
F1 score
Field-level accuracy
OCR
Character/text accuracy
Important medical-field accuracy
Summary
Factual consistency
Missing information rate
Hallucination rate
System
Processing time
Response latency
Successful session completion rate

The final presentation should show actual measured numbers rather than unsupported claims.

24. Development Phases

The project will be developed incrementally.

Phase 0 — Repository, Workspace & Development Setup
Status: COMPLETED

Completed:

Shared GitHub repository established
Existing project folder established as source of truth
VS Code used for repository/terminal operations
Antigravity used for coding
OpenCode extension used for bug finding/debugging
.env.example established
Actual .env kept local and excluded from GitHub
Shared folder structure established
Development rule

Antigravity, VS Code and OpenCode must operate on the same physical project directory.

AI coding tools must not create duplicate project folders or parallel architectures.

Before creating a new file, existing project structure should be inspected.

Do not rename/move architectural files without team agreement.

25. Phase 1 — Database Schema & Data Model
Status: SCHEMA DESIGN COMPLETED — IMPLEMENTATION PENDING

The following collections have been finalized:

patients
doctors
sessions
clinical_histories
responses
documents
extracted_information
timeline_events
case_summaries

Relationships have been defined.

The database is the break point between the patient and doctor workflows.

Next tasks:

Implement database connection
Implement models/schemas
Add indexes where required
Test CRUD operations
Connect models to FastAPI
## 26. Phase 2 — API & JSON Contracts

**Status: CONTRACT DESIGN COMPLETED — IMPLEMENTATION PENDING**

The detailed API, JSON, AI, OCR, validation, and frontend/backend communication contracts are defined in:

`docs/API_CONTRACTS.md`

`docs/API_CONTRACTS.md` is the single technical source of truth for API and JSON communication.

The following have been defined:

* API base structure
* HTTP methods
* Standard success response
* Standard error response
* Error codes
* Application ID conventions
* Date/time conventions
* Language codes
* Patient API contracts
* Doctor API contracts
* Authentication API structure
* Session API contracts
* Response API contracts
* Clinical history contracts
* Source-traceability contracts
* Document API contracts
* Medical information extraction contracts
* Timeline contracts
* Case summary contracts
* Doctor record contracts
* Doctor editing/approval contracts
* Clinical question contracts
* AI input/output contracts
* OCR input/output contracts
* Validation rules
* Contract change rules

### Phase 2 implementation tasks

1. Create the FastAPI API structure.
2. Create Pydantic request/response schemas.
3. Implement standard API response and error structures.
4. Implement database connection and required models.
5. Implement the agreed patient/session/response/history/document/timeline/summary/doctor endpoints as appropriate for the current development phase.
6. Ensure API structures match `docs/API_CONTRACTS.md`.
7. Add validation for required fields, data types, enums, IDs, and dates.
8. Add basic API testing.
9. Verify the APIs through FastAPI Swagger/OpenAPI documentation.
10. Update this document when Phase 2 implementation is fully tested and completed.

### Important

Phase 2 implementation must establish the contracts without prematurely implementing the complete AI, OCR, voice, adaptive questioning, or doctor UI features belonging to later phases.

AI and OCR integrations should follow the contracts defined in `docs/API_CONTRACTS.md` when those modules are implemented.


27. Phase 3 — Basic Patient Flow
Status: NOT STARTED

Build the minimum working patient flow:

Registration
     ↓
Authentication
     ↓
Language
     ↓
Start Session
     ↓
Questions
     ↓
Save Responses
     ↓
Retrieve Session

The first goal is a working non-AI flow.

28. Phase 4 — Clinical Question Engine & Adaptive Questioning
Status: NOT STARTED

Implement the structured clinical question framework.

Tasks:

Define question schemas
Define clinical fields
Define required/optional fields
Define branching rules
Define complaint-specific questioning
Connect patient responses to the question engine
Add Gemini only where natural-language understanding is required

Architecture:

Clinical Framework
       ↓
Determine missing information
       ↓
Select next question
       ↓
Patient answer
       ↓
AI understands answer
       ↓
Structured response
       ↓
Repeat

The LLM should not freely control the entire interview.

29. Phase 5 — Voice Input
Status: NOT STARTED

Implement:

Patient speaks
      ↓
Speech-to-text
      ↓
Text response
      ↓
AI structuring
      ↓
Save response

Tasks:

Browser/audio input
Speech-to-text integration
Indian-language testing
Error handling
Voice/text switching
Language handling

Text/touch input must remain available as a fallback.

30. Phase 6 — Medical Documents & OCR
Status: NOT STARTED

Implement:

Upload
   ↓
File processing
   ↓
OCR / Vision
   ↓
Extract text
   ↓
Medical information extraction
   ↓
Structured JSON
   ↓
Database

Tasks:

Document upload
File validation
OCR integration
Text extraction
Medical entity extraction
Medication extraction
Investigation extraction
Date extraction
Document status tracking
Error handling
31. Phase 7 — Patient Timeline
Status: NOT STARTED

Implement:

Patient information
       +
Document information
       ↓
Date extraction
       ↓
Timeline events
       ↓
Chronological ordering

Tasks:

Define event types
Extract dates
Create timeline events
Sort events chronologically
Connect each event to its source
32. Phase 8 — AI Case Summary
Status: NOT STARTED

Implement:

Clinical History
       +
Relevant Extracted Information
       +
Timeline
       ↓
AI Case Summary
       ↓
Case Summary stored in MongoDB

The summary must:

Be concise
Be structured
Preserve source information where applicable
Avoid diagnosis
Avoid hallucinated information
Clearly distinguish reported information from inferred content
33. Phase 9 — Doctor Workflow
Status: NOT STARTED

Implement:

Doctor Login
      ↓
Dashboard
      ↓
Patient List
      ↓
Patient Record
      ↓
Case Summary
      ↓
Relevant History
      ↓
Documents
      ↓
Full History
      ↓
Edit
      ↓
Approve

The dashboard should prioritize relevant information rather than displaying the entire record at once.

34. Phase 10 — Authentication & Security
Status: NOT STARTED

Implement:

Patient authentication
Doctor authentication
Password hashing
JWT/session handling
Protected routes
Role-based access
Input validation
Secure environment variables
Document access protection
35. Phase 11 — Integration
Status: NOT STARTED

Connect all modules:

Frontend
   ↓
FastAPI
   ↓
MongoDB
   ↓
AI
   ├── Questioning
   ├── Extraction
   └── Summarization
   ↓
OCR
   ↓
Timeline
   ↓
Doctor Dashboard

Test the complete patient-to-doctor workflow.

36. Phase 12 — Differentiation & ML Improvements
Status: NOT STARTED

Only after the baseline system works.

Potential work:

Clinical history synthetic dataset
Multilingual/Hinglish testing
Medical document benchmark
Source-linked information
Specialized information-extraction model
Evaluation metrics
Baseline vs specialized-model comparison

The specialized ML model is optional.

The project must not sacrifice a working MVP for an unfinished ML model.

37. Phase 13 — Testing & Evaluation
Status: NOT STARTED

Test:

Patient registration
Authentication
Session persistence
Session resumption
Voice input
Text/touch input
Adaptive questioning
Document upload
OCR
Medical extraction
Timeline generation
Summary generation
Doctor dashboard
Editing/approval
Multilingual inputs
Error handling

Create measurable evaluation results.

38. Phase 14 — Deployment
Status: NOT STARTED

Target deployment:

Frontend → Vercel
Backend  → Render
Database → MongoDB Atlas

Tasks:

Production environment variables
Backend deployment
Frontend deployment
MongoDB production configuration
CORS configuration
API URL configuration
File storage configuration
End-to-end production testing
39. Phase 15 — SIH Internal Demo Preparation
Status: NOT STARTED

Prepare:

Final working prototype
Demo patient data
Demo medical documents
Doctor account
Patient account
Complete demo flow
Architecture diagram
Database diagram
AI pipeline diagram
Dataset/evaluation results
Technology explanation
Differentiation explanation
Limitations
Future scope
Presentation/PPT
Demo script

The demo should prioritize a reliable working flow over unfinished advanced features.

40. Recommended File Structure
patient-case-taking/
│
├── README.md
├── PROJECT_CONTEXT.md
├── .gitignore
├── .env.example
│
├── frontend/
│   ├── package.json
│   ├── app/
│   │   ├── page.tsx
│   │   ├── patient/
│   │   │   ├── register/
│   │   │   ├── language/
│   │   │   ├── history/
│   │   │   └── documents/
│   │   │
│   │   └── doctor/
│   │       ├── login/
│   │       ├── dashboard/
│   │       └── patient/
│   │
│   ├── components/
│   │   ├── patient/
│   │   ├── doctor/
│   │   └── common/
│   │
│   ├── services/
│   │   └── api.ts
│   │
│   └── types/
│       └── index.ts
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── patient.py
│   │   ├── doctor.py
│   │   ├── history.py
│   │   ├── documents.py
│   │   └── summary.py
│   │
│   ├── ai/
│   │   ├── questioning/
│   │   ├── extraction/
│   │   └── summarization/
│   │
│   ├── services/
│   │   ├── ocr/
│   │   ├── speech/
│   │   └── timeline/
│   │
│   ├── models/
│   │   ├── patient.py
│   │   ├── doctor.py
│   │   ├── session.py
│   │   ├── response.py
│   │   ├── history.py
│   │   ├── document.py
│   │   ├── extraction.py
│   │   ├── timeline.py
│   │   └── summary.py
│   │
│   ├── database/
│   │   └── connection.py
│   │
│   └── utils/
│       ├── auth.py
│       └── validators.py
│
├── uploads/
│
├── data/
│   ├── clinical_cases/
│   └── document_samples/
│
└── tests/
    ├── frontend/
    └── backend/
41. Team Development Rule

Six people will work simultaneously.

Each person should primarily work within their assigned module/folder.

Avoid having multiple people constantly modify:

main.py
api.ts
shared components
database connection

Use Git branches.

Recommended workflow:

main
 │
 ├── feature/patient
 ├── feature/doctor
 ├── feature/ai
 ├── feature/documents
 └── feature/backend

Before starting work:

git pull

After completing a logical task:

git add .
git commit -m "Describe the change"
git push

Merge tested features into main.

42. AI Coding Tool Rules

The project uses:

VS Code
    ↓
Repository + Terminal + Git

Antigravity
    ↓
Primary coding

OpenCode
    ↓
Bug finding / debugging

All three tools must operate on the same project directory.

Mandatory rules for AI coding agents
Inspect the existing project structure before creating files.
Do not create duplicate folders.
Do not create alternative versions of existing files.
Do not rename files without explicit approval.
Do not move files without explicit approval.
Follow the existing architecture.
Reuse existing models, services and utilities.
Do not independently invent new JSON formats.
Do not install unnecessary dependencies.
Do not modify another person's module unless required and discussed.
Keep API contracts consistent with the agreed database schema.
Never hard-code API keys or secrets.
Run tests/build checks after major changes.
Keep changes small and logically grouped.
43. Important Project Decisions

These decisions are currently finalized:

The system is a pre-consultation clinical history and documentation system.
It does not diagnose patients.
Red-flag detection is removed.
Patient and doctor workflows are independent.
The database separates the patient workflow from the doctor workflow.
Patient progress should be saved throughout the interaction.
The doctor accesses the saved record later.
The doctor should see a concise, relevant summary first.
Full history and original documents remain available.
Doctor editing/approval is available but should not become a lengthy verification task.
Clinical rules/framework determine what information should be collected.
AI helps understand and structure natural-language responses.
AI should not freely control the entire medical interview.
Source information should be retained for important extracted facts.
A specialized ML model is an optional later improvement, not a first step.
Synthetic data will be preferred for prototype testing where real patient data is unavailable.
Differentiation should come primarily from implementation quality, evaluation, reliability, multilingual support, source traceability, and technical methodology rather than adding excessive features.
Patient and doctor workflows are separated by persistent database state.
A session represents an individual patient interaction/visit.
Raw voice recordings should not be stored unnecessarily.
AI-generated information should remain traceable to patient responses or documents where possible.
The doctor should not be required to individually verify every AI-generated field.
The application should prioritize relevant information rather than displaying the entire medical record on the main dashboard.
A working baseline system must be completed before attempting advanced ML differentiation.
44. Current Project Status
Phase 0 — Repository / Workspace / Development Setup

Status: COMPLETED

GitHub repository established
Shared project structure established
VS Code workflow established
Antigravity workflow established
OpenCode workflow established
.env.example established
.env kept local
Same-folder development rule established
Phase 1 — Database Schema & Data Model

Status: SCHEMA DESIGN COMPLETED

Final collections:

patients
doctors
sessions
clinical_histories
responses
documents
extracted_information
timeline_events
case_summaries

Relationships finalized.

Database implementation remains pending.

Phase 2 — API & JSON Contracts

Status: CONTRACT DESIGN COMPLETED — IMPLEMENTATION PENDING

API structure defined
JSON response format defined
Patient/session/history contracts defined
Document/OCR contracts defined
AI contracts defined
Timeline/summary contracts defined
Doctor contracts defined
Validation rules defined
Detailed specification stored in docs/API_CONTRACTS.md

Phase 3 — Basic Patient Flow

Status: NOT STARTED

Phase 4 — Clinical Question Engine & Adaptive Questioning

Status: NOT STARTED

Phase 5 — Voice Input

Status: NOT STARTED

Phase 6 — Medical Documents & OCR

Status: NOT STARTED

Phase 7 — Patient Timeline

Status: NOT STARTED

Phase 8 — AI Case Summary

Status: NOT STARTED

Phase 9 — Doctor Workflow

Status: NOT STARTED

Phase 10 — Authentication & Security

Status: NOT STARTED

Phase 11 — Integration

Status: NOT STARTED

Phase 12 — Differentiation & ML Improvements

Status: NOT STARTED

Phase 13 — Testing & Evaluation

Status: NOT STARTED

Phase 14 — Deployment

Status: NOT STARTED

Phase 15 — SIH Internal Demo Preparation

Status: NOT STARTED

## 45. Immediate Next Step

The project is now entering **Phase 2 implementation**.

The API and JSON contract design has been completed and documented in:

`docs/API_CONTRACTS.md`

The immediate technical goal is to implement and test the agreed backend contracts without changing the architecture.

Development sequence:

```text
Database Schema
        ↓
API Contracts
        ↓
Pydantic Request/Response Schemas
        ↓
FastAPI Routes
        ↓
Database Connection
        ↓
Validation
        ↓
API Testing
        ↓
Phase 2 Completion
        ↓
Phase 3 — Basic Patient Flow
```

The implementation must follow `docs/API_CONTRACTS.md`.

No developer or AI coding tool should independently create alternative JSON structures or API endpoints.


46. Project Guiding Principles

The project should prioritize:

Reliability > Feature count

Clinical information organization > Diagnosis

Traceability > Black-box AI

Simple working prototype > Large unfinished system

Real evaluation > Unsupported claims

Shared contracts > Independent implementations

One repository > Multiple parallel architectures

