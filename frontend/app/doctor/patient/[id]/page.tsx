"use client";

import { use, useSyncExternalStore } from "react";
import PatientRecordView from "@/components/doctor/PatientRecordView";

function getDoctorIdSnapshot() {
  if (typeof window === "undefined") return "DOC-000001";
  return localStorage.getItem("doctor_id") || "DOC-000001";
}

function subscribeDoctorId(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

export default function PatientRecordPage({
  params,
}: {
  params: Promise<{ id: string }> | { id: string };
}) {
  const resolvedParams = "then" in params ? use(params as Promise<{ id: string }>) : params;
  const doctorId = useSyncExternalStore(
    subscribeDoctorId,
    getDoctorIdSnapshot,
    () => "DOC-000001"
  );

  return <PatientRecordView doctorId={doctorId} patientId={resolvedParams.id} />;
}
