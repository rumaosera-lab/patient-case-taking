// components/doctor/DoctorDashboard.tsx

"use client";

import { useEffect, useState } from "react";
import { getDoctorPatients, type DoctorPatientRecord } from "@/services/doctorApi";
import PatientListItem from "./PatientListItem";

export default function DoctorDashboard({ doctorId }: { doctorId: string }) {
  const [records, setRecords] = useState<DoctorPatientRecord[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      const res = await getDoctorPatients(doctorId);
      if (res.success) {
        // Per API_CONTRACTS.md Sec 21: backend returns an array of full
        // records (patient + current_session + case_summary +
        // relevant_history + timeline + documents), with READY_FOR_DOCTOR
        // sessions prioritized first. We trust that order — no
        // client-side re-sorting.
        setRecords(res.data || []);
      } else {
        setError(res.error?.message || "Failed to load patient records");
      }
      setLoading(false);
    }
    load();
  }, [doctorId]);

  const filtered = records.filter((rec) => {
    const p = rec?.patient;
    if (!p) return false;
    const name = p.name || "";
    const pid = p.patient_id || "";
    return (
      name.toLowerCase().includes(search.toLowerCase()) ||
      pid.toLowerCase().includes(search.toLowerCase())
    );
  });

return (
  <div className="min-h-screen bg-[#F7FCF8] text-[#123F3B]">
    <div className="mx-auto w-full max-w-[1120px] px-6 py-10 sm:px-8">
      <div className="mb-8">
        <h1 className="text-[28px] font-medium tracking-[-0.02em] text-[#123F3B]">
          Doctor Dashboard
        </h1>

        <p className="mt-1 text-[14px] text-[#6E8985]">
          Patients awaiting review
        </p>
      </div>

      <input
        type="text"
        placeholder="Search by name or patient ID..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="
          mb-7
          h-[50px]
          w-full
          rounded-[14px]
          border
          border-[#D7E7E2]
          bg-white
          px-4
          text-[14px]
          text-[#123F3B]
          outline-none
          placeholder:text-[#9AAFAC]
          focus:border-[#4D9188]
          focus:ring-2
          focus:ring-[#4D9188]/10
        "
      />

      {loading && (
        <p className="px-1 py-6 text-[14px] text-[#7B9691]">
          Loading patients...
        </p>
      )}

      {error && (
        <p className="px-1 py-6 text-[14px] text-[#B85D4D]">
          {error}
        </p>
      )}

      <div className="flex flex-col gap-3">
        {filtered.map(({ patient, current_session }) => (
          <PatientListItem
            key={patient.patient_id}
            patient={patient}
            session={current_session}
          />
        ))}

        {!loading && filtered.length === 0 && (
          <p className="py-12 text-center text-[14px] text-[#7B9691]">
            No patients found.
          </p>
        )}
      </div>
    </div>
  </div>
);
}
