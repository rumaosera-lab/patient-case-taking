// app/doctor/patient/[id]/page.tsx

"use client";

import { useEffect, useState } from "react";
import PatientRecordView from "@/components/doctor/PatientRecordView";

export default function PatientRecordPage({
  params,
}: {
  params: { id: string };
}) {
  const [doctorId, setDoctorId] = useState<string>("DOC-000001");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("doctor_id");
      if (stored) {
        setDoctorId(stored);
      }
    }
  }, []);

  return <PatientRecordView doctorId={doctorId} patientId={params.id} />;
}
