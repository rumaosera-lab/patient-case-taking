// app/doctor/dashboard/page.tsx

"use client";

import { useEffect, useState } from "react";
import DoctorDashboard from "@/components/doctor/DoctorDashboard";

export default function DashboardPage() {
  const [doctorId, setDoctorId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Read doctorId from localStorage (set by LoginForm after successful login)
    const stored = localStorage.getItem("doctor_id");
    setDoctorId(stored || "DOC-000001"); // fallback for demo/testing
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F7FCF8] flex items-center justify-center">
        <p className="text-[14px] text-[#718A86]">Loading...</p>
      </div>
    );
  }

  if (!doctorId) {
    return (
      <div className="min-h-screen bg-[#F7FCF8] flex items-center justify-center">
        <p className="text-[14px] text-[#B65F50]">Doctor ID not found. Please log in.</p>
      </div>
    );
  }

  return <DoctorDashboard doctorId={doctorId} />;
}
