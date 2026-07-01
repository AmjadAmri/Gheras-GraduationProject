import { useState } from "react";
import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Sidebar } from "../components/Sidebar";
import { OnboardingTour } from "../components/OnboardingTour";
import { Menu } from "lucide-react";

export function DashboardLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="h-10 w-10 rounded-full border-4 border-primary/20 border-t-sidebar animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/sign-in" replace />;
  }

  return (
    <div className="min-h-screen bg-surface">
      <Sidebar mobileOpen={sidebarOpen} onMobileClose={() => setSidebarOpen(false)} />

      {/* Mobile top bar */}
      <div className="sticky top-0 z-30 flex items-center gap-3 bg-surface/80 backdrop-blur-sm px-4 py-3 lg:hidden">
        <button
          onClick={() => setSidebarOpen(true)}
          className="rounded-lg p-2 text-gray-600 hover:bg-gray-200 transition-colors cursor-pointer"
        >
          <Menu className="h-5 w-5" />
        </button>
        <span className="text-sm font-semibold text-gray-900">غراس</span>
      </div>

      <main className="lg:ps-64">
        <div className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      <OnboardingTour />
    </div>
  );
}
