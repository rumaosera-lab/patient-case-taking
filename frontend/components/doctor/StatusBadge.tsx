// components/doctor/StatusBadge.tsx

import type { SessionStatus } from "@/services/doctorApi";

const STYLES: Record<SessionStatus, string> = {
  IN_PROGRESS:
    "border-[#D5E8E3] bg-[#EDF7F4] text-[#367A72]",
  PROCESSING:
    "border-[#D5E8E3] bg-[#EDF7F4] text-[#367A72]",
  COMPLETED:
    "border-[#D5E8E3] bg-[#EDF7F4] text-[#367A72]",
  READY_FOR_DOCTOR:
    "border-[#F0D6CE] bg-[#FFF3EF] text-[#B75E4E]",
  REVIEWED:
    "border-[#D5E8E3] bg-[#EDF7F4] text-[#367A72]",
};

const LABELS: Record<SessionStatus, string> = {
  IN_PROGRESS: "In Progress",
  PROCESSING: "Processing",
  COMPLETED: "Completed",
  READY_FOR_DOCTOR: "Ready for Review",
  REVIEWED: "Reviewed",
};

export default function StatusBadge({ status }: { status: SessionStatus }) {
  return (
    <span
      className={`
        inline-flex
        items-center
        rounded-full
        border
        px-3
        py-[6px]
        text-[10px]
        font-medium
        tracking-[0.02em]
        ${STYLES[status]}
      `}
    >
      {LABELS[status]}
    </span>
  );
}
