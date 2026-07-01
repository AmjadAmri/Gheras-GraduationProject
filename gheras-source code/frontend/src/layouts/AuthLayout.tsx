import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import gherasLogo from "../assets/gheras-logo.png";

export function AuthLayout() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sidebar via-sidebar-hover to-sidebar flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -end-40 h-80 w-80 rounded-full bg-white/5" />
        <div className="absolute -bottom-20 -start-20 h-60 w-60 rounded-full bg-white/5" />
        <div className="absolute top-1/2 start-1/4 h-40 w-40 rounded-full bg-accent-gold/10" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="inline-flex h-24 w-24 items-center justify-center rounded-3xl bg-white/20 backdrop-blur-sm mb-4 p-3 shadow-lg">
            <img src={gherasLogo} alt="غراس" className="h-full w-full object-contain" />
          </div>
          <h1 className="text-3xl font-bold text-white">غراس</h1>
          <p className="text-white/70 mt-1">قصص ذكية تنمو مع أطفالك</p>
        </div>

        <div className="rounded-2xl bg-white p-8 shadow-2xl">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
