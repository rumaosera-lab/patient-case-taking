"use client";

import { useSyncExternalStore } from "react";
import DoctorDashboard from "@/components/doctor/DoctorDashboard";

function getDoctorIdSnapshot() {
  if (typeof window === "undefined") return "DOC-000001";
  return localStorage.getItem("doctor_id") || "DOC-000001";
}

function subscribeDoctorId(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

export default function DashboardPage() {
  const doctorId = useSyncExternalStore(
    subscribeDoctorId,
    getDoctorIdSnapshot,
    () => "DOC-000001"
  );

  return <DoctorDashboard doctorId={doctorId} />;
}
