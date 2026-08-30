// components/doctor/LoginForm.tsx

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginDoctor } from "@/services/doctorApi";

export default function LoginForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const res = await loginDoctor(email, password);
    setLoading(false);

    if (res.success) {
      // Store token in localStorage (placeholder approach)
      // NOTE: This will be replaced by a proper auth context/session manager in Phase 10
      localStorage.setItem("auth_token", res.data.access_token);
      localStorage.setItem("doctor_id", res.data.user.user_id);

      // Redirect to dashboard
      router.push("/doctor/dashboard");
    } else {
      setError(res.error.message);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-[16px] border border-[#DCE9E5] bg-white p-6">
      {/* Email field */}
      <div className="mb-6">
        <label className="mb-2 block text-[10px] font-medium uppercase tracking-[0.12em] text-[#829B96]">
          Email Address
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="doctor@example.com"
          required
          className="
            h-[52px]
            w-full
            rounded-[15px]
            border
            border-[#DCE9E5]
            bg-white
            px-4
            text-[14px]
            text-[#123F3B]
            placeholder:text-[#91A5A1]
            outline-none
            transition-colors
            focus:border-[#08766D]
            focus:ring-2
            focus:ring-[#08766D]/10
          "
        />
      </div>

      {/* Password field */}
      <div className="mb-8">
        <label className="mb-2 block text-[10px] font-medium uppercase tracking-[0.12em] text-[#829B96]">
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          required
          className="
            h-[52px]
            w-full
            rounded-[15px]
            border
            border-[#DCE9E5]
            bg-white
            px-4
            text-[14px]
            text-[#123F3B]
            placeholder:text-[#91A5A1]
            outline-none
            transition-colors
            focus:border-[#08766D]
            focus:ring-2
            focus:ring-[#08766D]/10
          "
        />
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 rounded-[12px] border border-[#F1D8D1] bg-[#FFF3EF] px-4 py-3">
          <p className="text-[13px] text-[#B65F50]">{error}</p>
        </div>
      )}

      {/* Submit button */}
      <button
        type="submit"
        disabled={loading}
        className="
          w-full
          rounded-[12px]
          bg-[#08766D]
          px-4
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
        {loading ? "Logging in..." : "Log In"}
      </button>

      {/* Info text */}
      <p className="mt-6 text-center text-[12px] text-[#829B96]">
        Demo credentials: Use any email/password (API handles validation)
      </p>

      {/* Return to Patient Kiosk */}
      <div className="mt-4 text-center">
        <Link
          href="/"
          className="text-[13px] font-medium text-[#08766D] hover:underline"
        >
          ← Return to Patient MediKiosk
        </Link>
      </div>
    </form>
  );
}
