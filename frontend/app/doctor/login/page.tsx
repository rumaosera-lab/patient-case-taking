// app/doctor/login/page.tsx

import LoginForm from "@/components/doctor/LoginForm";

export default function DoctorLoginPage() {
  return (
    <div className="min-h-screen bg-[#F7FCF8] text-[#123F3B]">
      <div className="mx-auto w-full max-w-[760px] px-6 py-12 sm:py-16">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-[28px] font-medium tracking-[-0.025em] text-[#123F3B]">
            Doctor Login
          </h1>
          <p className="mt-2 text-[14px] text-[#718A86]">
            Access your patient records and review cases.
          </p>
        </div>

        {/* Login Form */}
        <LoginForm />
      </div>
    </div>
  );
}
