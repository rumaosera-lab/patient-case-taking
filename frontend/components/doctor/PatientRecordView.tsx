// components/doctor/PatientRecordView.tsx
//
// Renders the full doctor-facing patient record with inline editing (Job 2).
// Doctors can edit any field → Save sends PATCH to backend with changed fields only.
// Cancel discards local edits. No audit trail for MVP (existing source traceability preserved).

"use client";

import { useEffect, useState } from "react";
import {
  getDoctorPatientRecord,
  approveSession,
  updateSessionHistory,
  type DoctorPatientRecord,
} from "@/services/doctorApi";

interface Props {
  doctorId: string;
  patientId: string;
}

export default function PatientRecordView({ doctorId, patientId }: Props) {
  const [record, setRecord] = useState<DoctorPatientRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);

  // Inline editing state
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, unknown>>({});
  const [savingField, setSavingField] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      const res = await getDoctorPatientRecord(doctorId, patientId);
      if (res.success) {
        setRecord(res.data);
      } else {
        setError(res.error?.message || "Failed to load patient record");
      }
      setLoading(false);
    }
    load();
  }, [doctorId, patientId]);

  async function handleApprove() {
    if (!record || !record.current_session?.session_id) return;
    setApproving(true);
    const res = await approveSession(record.current_session.session_id);
    setApproving(false);
    if (res.success) {
      setRecord({
        ...record,
        current_session: {
          ...(record.current_session || {}),
          status: res.data.status,
        },
        case_summary: {
          ...(record.case_summary || {}),
          review_status: res.data.review_status,
          reviewed_by: res.data.reviewed_by,
          approved_at: res.data.approved_at,
        },
      });
    } else {
      setError(res.error?.message || "Failed to approve session");
    }
  }

  function startEdit(fieldName: string, currentValue: unknown) {
    setEditingField(fieldName);
    setEditValues({ [fieldName]: currentValue });
  }

  function cancelEdit() {
    setEditingField(null);
    setEditValues({});
  }

  async function saveEdit(fieldName: string) {
    if (!record || !record.current_session?.session_id) return;
    setSavingField(fieldName);
    setError(null);

    const newValue = editValues[fieldName];
    let patchPayload: Record<string, unknown> = {};

    // Transform edited UI value to match API_CONTRACTS.md & backend ClinicalHistoryUpdate schema
    if (fieldName === "chief_complaint") {
      patchPayload = {
        chief_complaint: {
          value: typeof newValue === "string" ? newValue : "",
          source: { type: "previous_record", source_id: doctorId },
        },
      };
    } else if (fieldName === "history_of_present_illness") {
      patchPayload = {
        history_of_present_illness: {
          description: {
            value: typeof newValue === "string" ? newValue : "",
            source: { type: "previous_record", source_id: doctorId },
          },
        },
      };
    } else if (fieldName === "relevant_history") {
      const arr = Array.isArray(newValue) ? newValue : [String(newValue || "")];
      patchPayload = {
        past_medical_history: arr.map((item) => ({
          condition: item,
          value: item,
        })),
      };
    } else if (fieldName === "current_medications") {
      const arr = Array.isArray(newValue) ? newValue : [String(newValue || "")];
      patchPayload = {
        current_medications: arr.map((item) => ({
          medicine: item,
          value: item,
        })),
      };
    } else if (fieldName === "relevant_investigations") {
      const arr = Array.isArray(newValue) ? newValue : [String(newValue || "")];
      patchPayload = {
        review_of_systems: arr.map((item) => ({
          finding: item,
          value: item,
        })),
      };
    } else if (fieldName === "allergies") {
      const valStr = typeof newValue === "string" ? newValue : "";
      patchPayload = {
        allergies: valStr.trim()
          ? [{ allergen: valStr, value: valStr }]
          : [],
      };
    } else {
      patchPayload = { [fieldName]: newValue };
    }

    const res = await updateSessionHistory(
      record.current_session.session_id,
      patchPayload
    );

    setSavingField(null);

    if (res.success) {
      // Update local state with new clinical history returned from PATCH /history
      setRecord({
        ...record,
        relevant_history: res.data,
      });
      setEditingField(null);
      setEditValues({});
    } else {
      setError(res.error?.message || "Failed to update clinical history");
    }
  }

  if (loading)
    return (
      <div className="min-h-screen bg-[#F7FCF8]">
        <p className="px-6 py-8 text-[14px] text-[#718A86]">Loading record...</p>
      </div>
    );
  if (error)
    return (
      <div className="min-h-screen bg-[#F7FCF8]">
        <p className="px-6 py-8 text-[14px] text-[#B65F50]">{error}</p>
      </div>
    );
  if (!record) return null;

  const patient = record.patient || {
    patient_id: patientId,
    name: "Unknown Patient",
    gender: "-",
    date_of_birth: "-",
    phone: "-",
    preferred_language: "en",
    abha_id: null,
  };
  const current_session = record.current_session || {
    session_id: "",
    patient_id: patientId,
    status: "IN_PROGRESS" as const,
    department: "General Medicine",
    started_at: "",
    completed_at: null,
    last_updated_at: "",
  };
  const case_summary = record.case_summary || {
    summary_id: "",
    patient_id: patientId,
    session_id: current_session.session_id,
    summary_text: "",
    structured_summary: {
      chief_complaint: "",
      history_of_present_illness: "",
      relevant_history: [],
      current_medications: [],
      relevant_investigations: [],
      allergies: "",
    },
    generated_at: "",
    reviewed_by: null,
    review_status: "GENERATED" as const,
    doctor_notes: null,
    approved_at: null,
  };
  const s = case_summary.structured_summary || {
    chief_complaint: "",
    history_of_present_illness: "",
    relevant_history: [],
    current_medications: [],
    relevant_investigations: [],
    allergies: "",
  };
  const timeline = Array.isArray(record.timeline) ? record.timeline : [];
  const documents = Array.isArray(record.documents) ? record.documents : [];
  const rh = record.relevant_history as unknown as Record<string, unknown> | undefined;

  // -------------------------------------------------------------------------
  // Resolve field values: Prioritize persisted relevant_history with case_summary fallback
  // -------------------------------------------------------------------------

  // 1. Chief Complaint
  let resolvedChiefComplaint = s.chief_complaint || "";
  if (rh?.chief_complaint) {
    if (typeof rh.chief_complaint === "string" && rh.chief_complaint.trim()) {
      resolvedChiefComplaint = rh.chief_complaint;
    } else if (
      typeof rh.chief_complaint === "object" &&
      "value" in rh.chief_complaint &&
      rh.chief_complaint.value
    ) {
      resolvedChiefComplaint = String(rh.chief_complaint.value);
    }
  }

  // 2. History of Present Illness (HPI)
  let resolvedHpi = s.history_of_present_illness || "";
  if (rh?.history_of_present_illness) {
    if (
      typeof rh.history_of_present_illness === "string" &&
      rh.history_of_present_illness.trim()
    ) {
      resolvedHpi = rh.history_of_present_illness;
    } else if (typeof rh.history_of_present_illness === "object") {
      const hpiObj = rh.history_of_present_illness as Record<string, unknown>;
      if (
        hpiObj.description &&
        typeof hpiObj.description === "object" &&
        "value" in (hpiObj.description as { value: unknown })
      ) {
        resolvedHpi = String((hpiObj.description as { value: unknown }).value);
      } else {
        const parts = Object.entries(hpiObj)
          .map(([k, v]) => {
            if (v && typeof v === "object" && "value" in (v as { value: unknown })) {
              return `${k}: ${(v as { value: unknown }).value}`;
            }
            return v ? `${k}: ${v}` : null;
          })
          .filter(Boolean);
        if (parts.length > 0) {
          resolvedHpi = parts.join("; ");
        }
      }
    }
  }

  // 3. Relevant History (Past Medical History)
  let resolvedRelevantHistory: string[] = Array.isArray(s.relevant_history)
    ? s.relevant_history
    : [];
  if (
    Array.isArray(rh?.past_medical_history) &&
    rh.past_medical_history.length > 0
  ) {
    resolvedRelevantHistory = rh.past_medical_history
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const rec = item as Record<string, unknown>;
          return String(rec.condition || rec.value || rec.name || JSON.stringify(item));
        }
        return String(item);
      })
      .filter(Boolean);
  }

  // 4. Current Medications
  let resolvedMedications: string[] = Array.isArray(s.current_medications)
    ? s.current_medications
    : [];
  if (
    Array.isArray(rh?.current_medications) &&
    rh.current_medications.length > 0
  ) {
    resolvedMedications = rh.current_medications
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const rec = item as Record<string, unknown>;
          if (rec.medicine) {
            const parts = [rec.medicine, rec.dosage, rec.frequency].filter(Boolean);
            return parts.map(String).join(" ");
          }
          return String(rec.value || rec.name || JSON.stringify(item));
        }
        return String(item);
      })
      .filter(Boolean);
  }

  // 5. Relevant Investigations (Review of Systems)
  let resolvedInvestigations: string[] = Array.isArray(s.relevant_investigations)
    ? s.relevant_investigations
    : [];
  if (
    Array.isArray(rh?.review_of_systems) &&
    rh.review_of_systems.length > 0
  ) {
    resolvedInvestigations = rh.review_of_systems
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const rec = item as Record<string, unknown>;
          return String(rec.finding || rec.value || rec.system || JSON.stringify(item));
        }
        return String(item);
      })
      .filter(Boolean);
  }

  // 6. Allergies
  let resolvedAllergies = s.allergies || "";
  if (Array.isArray(rh?.allergies) && rh.allergies.length > 0) {
    resolvedAllergies = rh.allergies
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const rec = item as Record<string, unknown>;
          return String(rec.allergen || rec.value || rec.name || JSON.stringify(item));
        }
        return String(item);
      })
      .filter(Boolean)
      .join(", ");
  }

  return (
    <div className="min-h-screen bg-[#F7FCF8] text-[#123F3B]">
      <div className="mx-auto w-full max-w-[900px] px-6 py-10 sm:px-8">
        {/* Patient header */}
        <div className="mb-8">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-[0.12em] text-[#829B96]">
            {patient.patient_id}
          </p>
          <h1 className="text-[28px] font-medium tracking-[-0.025em] text-[#123F3B]">
            {patient.name}
          </h1>
          <p className="mt-2 text-[14px] text-[#718A86]">
            {patient.gender} &middot; DOB {patient.date_of_birth} &middot;{" "}
            {current_session.department}
          </p>
        </div>

        {/* Case Summary */}
        <section className="mb-8 rounded-[16px] border border-[#DCE9E5] bg-white p-6">
          <h2 className="mb-5 text-[14px] font-semibold uppercase tracking-[0.12em] text-[#829B96]">
            Case Summary
          </h2>

          <div className="space-y-5">
            <EditableField
              label="Chief Complaint"
              fieldName="chief_complaint"
              value={resolvedChiefComplaint}
              isEditing={editingField === "chief_complaint"}
              editValue={
                (editValues["chief_complaint"] as string) !== undefined
                  ? (editValues["chief_complaint"] as string)
                  : resolvedChiefComplaint
              }
              onEdit={() => startEdit("chief_complaint", resolvedChiefComplaint)}
              onCancel={cancelEdit}
              onSave={() => saveEdit("chief_complaint")}
              onChange={(v) => setEditValues({ ...editValues, chief_complaint: v })}
              isSaving={savingField === "chief_complaint"}
            />

            <EditableField
              label="History of Present Illness"
              fieldName="history_of_present_illness"
              value={resolvedHpi}
              isEditing={editingField === "history_of_present_illness"}
              editValue={
                (editValues["history_of_present_illness"] as string) !== undefined
                  ? (editValues["history_of_present_illness"] as string)
                  : resolvedHpi
              }
              onEdit={() =>
                startEdit("history_of_present_illness", resolvedHpi)
              }
              onCancel={cancelEdit}
              onSave={() => saveEdit("history_of_present_illness")}
              onChange={(v) =>
                setEditValues({ ...editValues, history_of_present_illness: v })
              }
              isSaving={savingField === "history_of_present_illness"}
              isTextarea
            />

            <EditableListField
              label="Relevant History"
              fieldName="relevant_history"
              items={resolvedRelevantHistory}
              isEditing={editingField === "relevant_history"}
              editValue={
                (editValues["relevant_history"] as string[]) !== undefined
                  ? (editValues["relevant_history"] as string[])
                  : resolvedRelevantHistory
              }
              onEdit={() => startEdit("relevant_history", resolvedRelevantHistory)}
              onCancel={cancelEdit}
              onSave={() => saveEdit("relevant_history")}
              onChange={(v) =>
                setEditValues({ ...editValues, relevant_history: v })
              }
              isSaving={savingField === "relevant_history"}
            />

            <EditableListField
              label="Current Medications"
              fieldName="current_medications"
              items={resolvedMedications}
              isEditing={editingField === "current_medications"}
              editValue={
                (editValues["current_medications"] as string[]) !== undefined
                  ? (editValues["current_medications"] as string[])
                  : resolvedMedications
              }
              onEdit={() => startEdit("current_medications", resolvedMedications)}
              onCancel={cancelEdit}
              onSave={() => saveEdit("current_medications")}
              onChange={(v) =>
                setEditValues({ ...editValues, current_medications: v })
              }
              isSaving={savingField === "current_medications"}
            />

            <EditableListField
              label="Relevant Investigations"
              fieldName="relevant_investigations"
              items={resolvedInvestigations}
              isEditing={editingField === "relevant_investigations"}
              editValue={
                (editValues["relevant_investigations"] as string[]) !== undefined
                  ? (editValues["relevant_investigations"] as string[])
                  : resolvedInvestigations
              }
              onEdit={() =>
                startEdit("relevant_investigations", resolvedInvestigations)
              }
              onCancel={cancelEdit}
              onSave={() => saveEdit("relevant_investigations")}
              onChange={(v) =>
                setEditValues({ ...editValues, relevant_investigations: v })
              }
              isSaving={savingField === "relevant_investigations"}
            />

            <EditableField
              label="Allergies"
              fieldName="allergies"
              value={resolvedAllergies}
              isEditing={editingField === "allergies"}
              editValue={
                (editValues["allergies"] as string) !== undefined
                  ? (editValues["allergies"] as string)
                  : resolvedAllergies
              }
              onEdit={() => startEdit("allergies", resolvedAllergies)}
              onCancel={cancelEdit}
              onSave={() => saveEdit("allergies")}
              onChange={(v) => setEditValues({ ...editValues, allergies: v })}
              isSaving={savingField === "allergies"}
            />
          </div>

          <div className="mt-6 border-t border-[#E5EFEC] pt-4">
            <p className="text-[12px] text-[#829B96]">
              Review status:{" "}
              <span className="font-semibold text-[#123F3B]">
                {case_summary.review_status}
              </span>
              {case_summary.approved_at && (
                <span className="text-[#829B96]">
                  {" "}
                  — approved {case_summary.approved_at}
                </span>
              )}
            </p>
          </div>
        </section>

        {/* Timeline */}
        <section className="mb-8">
          <h2 className="mb-5 text-[14px] font-semibold uppercase tracking-[0.12em] text-[#829B96]">
            Timeline
          </h2>
          {timeline.length === 0 && (
            <p className="text-[14px] text-[#718A86]">No timeline events recorded.</p>
          )}
          <div className="flex flex-col gap-4">
            {timeline.map((event) => (
              <div
                key={event.event_id}
                className="rounded-[16px] border border-[#DCE9E5] bg-white p-5"
              >
                <p className="mb-1 text-[10px] font-medium uppercase tracking-[0.12em] text-[#829B96]">
                  {event.event_date}
                </p>
                <p className="mb-2 text-[14px] font-semibold text-[#123F3B]">
                  {event.title}
                </p>
                <p className="mb-3 text-[14px] text-[#718A86]">{event.description}</p>
                <p className="text-[12px] text-[#829B96]">
                  Source: {event.source_type} ({event.source_id})
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Documents */}
        <section className="mb-8">
          <h2 className="mb-5 text-[14px] font-semibold uppercase tracking-[0.12em] text-[#829B96]">
            Documents
          </h2>
          {documents.length === 0 && (
            <p className="text-[14px] text-[#718A86]">No documents uploaded.</p>
          )}
          <div className="flex flex-col gap-3">
            {documents.map((doc) => {
              const apiBase =
                process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
              let docUrl = doc.file_url || `${apiBase}/documents/${doc.document_id}/file`;
              if (docUrl.startsWith("/")) {
                const backendOrigin = apiBase.replace(/\/api\/v1\/?$/, "");
                docUrl = `${backendOrigin}${docUrl}`;
              }
              return (
                <a
                  key={doc.document_id}
                  href={docUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="
                    flex
                    items-center
                    justify-between
                    rounded-[16px]
                    border
                    border-[#DCE9E5]
                    bg-white
                    px-5
                    py-4
                    transition-colors
                    hover:border-[#BDD5D0]
                    hover:bg-[#FBFDFC]
                  "
                >
                  <span className="text-[14px] font-medium text-[#123F3B]">
                    {doc.file_name}
                  </span>
                  <span className="text-[12px] text-[#829B96]">{doc.document_type}</span>
                </a>
              );
            })}
          </div>
        </section>

        {/* Approve action */}
        <div className="flex justify-end">
          <button
            onClick={handleApprove}
            disabled={approving || case_summary.review_status === "APPROVED"}
            className="
              rounded-[12px]
              bg-[#08766D]
              px-6
              py-3
              text-[14px]
              font-medium
              text-white
              transition-colors
              hover:bg-[#066960]
              disabled:opacity-50
              disabled:cursor-not-allowed
            "
          >
            {case_summary.review_status === "APPROVED"
              ? "Approved"
              : approving
              ? "Approving..."
              : "Approve"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Editable field components (Job 2)
// ============================================================================

interface EditableFieldProps {
  label: string;
  fieldName: string;
  value: string;
  isEditing: boolean;
  editValue: string;
  onEdit: () => void;
  onCancel: () => void;
  onSave: () => void;
  onChange: (value: string) => void;
  isSaving: boolean;
  isTextarea?: boolean;
}

function EditableField({
  label,
  value,
  isEditing,
  editValue,
  onEdit,
  onCancel,
  onSave,
  onChange,
  isSaving,
  isTextarea,
}: EditableFieldProps) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-[#829B96]">
          {label}
        </p>
        {!isEditing && (
          <button
            onClick={onEdit}
            className="text-[12px] text-[#08766D] hover:underline"
          >
            Edit
          </button>
        )}
      </div>

      {isEditing ? (
        <div>
          {isTextarea ? (
            <textarea
              value={editValue}
              onChange={(e) => onChange(e.target.value)}
              className="
                mb-2 w-full rounded-[12px] border border-[#08766D] bg-white
                p-3 text-[14px] text-[#123F3B] outline-none
              "
              rows={3}
            />
          ) : (
            <input
              type="text"
              value={editValue}
              onChange={(e) => onChange(e.target.value)}
              className="
                mb-2 h-[44px] w-full rounded-[12px] border border-[#08766D]
                bg-white px-3 text-[14px] text-[#123F3B] outline-none
              "
            />
          )}
          <div className="flex gap-2">
            <button
              onClick={onSave}
              disabled={isSaving}
              className="
                rounded-[8px] bg-[#08766D] px-3 py-2 text-[12px]
                font-medium text-white hover:bg-[#066960] disabled:opacity-50
              "
            >
              {isSaving ? "Saving..." : "Save"}
            </button>
            <button
              onClick={onCancel}
              disabled={isSaving}
              className="
                rounded-[8px] border border-[#DCE9E5] px-3 py-2 text-[12px]
                font-medium text-[#123F3B] hover:bg-[#EEF7F4] disabled:opacity-50
              "
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <p className="text-[14px] text-[#123F3B]">{value || "—"}</p>
      )}
    </div>
  );
}

interface EditableListFieldProps {
  label: string;
  fieldName: string;
  items: string[];
  isEditing: boolean;
  editValue: string[];
  onEdit: () => void;
  onCancel: () => void;
  onSave: () => void;
  onChange: (value: string[]) => void;
  isSaving: boolean;
}

function EditableListField({
  label,
  items,
  isEditing,
  editValue,
  onEdit,
  onCancel,
  onSave,
  onChange,
  isSaving,
}: EditableListFieldProps) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-[#829B96]">
          {label}
        </p>
        {!isEditing && (
          <button
            onClick={onEdit}
            className="text-[12px] text-[#08766D] hover:underline"
          >
            Edit
          </button>
        )}
      </div>

      {isEditing ? (
        <div>
          <div className="mb-2 flex flex-col gap-2">
            {editValue.map((item, i) => (
              <div key={i} className="flex gap-2">
                <input
                  type="text"
                  value={item}
                  onChange={(e) => {
                    const newItems = [...editValue];
                    newItems[i] = e.target.value;
                    onChange(newItems);
                  }}
                  className="
                    h-[40px] flex-1 rounded-[10px] border border-[#08766D]
                    bg-white px-3 text-[14px] text-[#123F3B] outline-none
                  "
                />
                <button
                  onClick={() => {
                    const newItems = editValue.filter((_, idx) => idx !== i);
                    onChange(newItems);
                  }}
                  className="
                    rounded-[10px] bg-[#FFF3EF] px-3 text-[12px] text-[#B65F50]
                    hover:bg-[#F1D8D1]
                  "
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={() => onChange([...editValue, ""])}
            className="
              mb-3 rounded-[8px] border border-[#DCE9E5] px-3 py-2 text-[12px]
              text-[#123F3B] hover:bg-[#EEF7F4]
            "
          >
            + Add item
          </button>
          <div className="flex gap-2">
            <button
              onClick={onSave}
              disabled={isSaving}
              className="
                rounded-[8px] bg-[#08766D] px-3 py-2 text-[12px]
                font-medium text-white hover:bg-[#066960] disabled:opacity-50
              "
            >
              {isSaving ? "Saving..." : "Save"}
            </button>
            <button
              onClick={onCancel}
              disabled={isSaving}
              className="
                rounded-[8px] border border-[#DCE9E5] px-3 py-2 text-[12px]
                font-medium text-[#123F3B] hover:bg-[#EEF7F4] disabled:opacity-50
              "
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          {items.length === 0 ? (
            <p className="text-[14px] text-[#718A86]">None reported</p>
          ) : (
            <ul className="space-y-1">
              {items.map((item, i) => (
                <li key={i} className="text-[14px] text-[#123F3B]">
                  • {item}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}