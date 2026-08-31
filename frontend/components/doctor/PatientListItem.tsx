// components/doctor/PatientListItem.tsx

import Link from "next/link";
import StatusBadge from "./StatusBadge";
import type { Patient, Session } from "@/services/doctorApi";

interface Props {
  patient: Patient;
  session: Session;
}

export default function PatientListItem({ patient, session }: Props) {
  const patientId = patient?.patient_id || "Unknown";
  const patientName = patient?.name || "Unnamed Patient";
  const department = session?.department || "General Medicine";
  const sessionStatus = session?.status || "READY_FOR_DOCTOR";

  return (
    <Link
      href={`/doctor/patient/${patientId}`}
      className="
        group
        flex
        items-center
        justify-between
        rounded-[16px]
        border
        border-[#D7E7E2]
        bg-white
        px-5
        py-[18px]
        transition-all
        duration-200
        hover:border-[#B9D4CE]
        hover:shadow-[0_4px_18px_rgba(18,63,59,0.06)]
      "
    >
      <div>
        <p className="mb-1 text-[10px] font-medium uppercase tracking-[0.12em] text-[#8AA19D]">
          {patientId}
        </p>

        <p className="text-[17px] font-semibold tracking-[-0.01em] text-[#123F3B]">
          {patientName}
        </p>

        <p className="mt-1 text-[13px] text-[#708A86]">
          {department}
        </p>
      </div>

      <StatusBadge status={sessionStatus} />
    </Link>
  );
}
