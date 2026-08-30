// app/doctor/dashboard/page.tsx

"use client";

import { useEffect, useState } from "react";
import DoctorDashboard from "@/components/doctor/DoctorDashboard";

export default function DashboardPage() {
  const [doctorId, setDoctorId] = useState<string>("DOC-000001");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("doctor_id");
      if (stored) {
        setDoctorId(stored);
      }
    }
  }, []);

  return <DoctorDashboard doctorId={doctorId} />;
}
