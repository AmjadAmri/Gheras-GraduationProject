import { NavLink } from "react-router-dom";
import { cn } from "../lib/cn";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  Users,
  Library,
  BarChart3,
  LogOut,
  Sparkles,
  X,
} from "lucide-react";
import { Avatar } from "./ui/Avatar";
import gherasLogo from "../assets/gheras-logo.png";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "الرئيسية", tourId: "" },
  { to: "/children", icon: Users, label: "الأطفال", tourId: "children" },
  { to: "/create-story", icon: Sparkles, label: "إنشاء قصة", tourId: "create-story" },
  { to: "/library", icon: Library, label: "المكتبة", tourId: "" },
  { to: "/progress", icon: BarChart3, label: "التقدم", tourId: "" },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const { user, signOut } = useAuth();

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={cn(
          "fixed inset-inline-start-0 top-0 z-40 flex h-screen w-64 flex-col bg-sidebar text-white transition-transform duration-300 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/15 p-2 shadow-sm backdrop-blur-sm">
              <img src={gherasLogo} alt="غراس" className="h-full w-full object-contain" />
            </div>
            <div>
              <h1 className="text-2xl font-bold leading-none">غراس</h1>
              <p className="text-sm text-white/75 mt-1">قصص ذكية لأطفالك</p>
            </div>
          </div>
          {/* Mobile close button */}
          <button
            onClick={onMobileClose}
            className="rounded-lg p-1.5 text-white/60 hover:bg-white/10 hover:text-white transition-colors cursor-pointer lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={onMobileClose}
              {...(item.tourId ? { "data-tour": item.tourId } : {})}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-white/20 text-white"
                    : "text-white/70 hover:bg-white/10 hover:text-white"
                )
              }
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 px-4 py-4">
          <div className="flex items-center gap-3">
            <Avatar name={user?.name || "م"} size="sm" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-white/60 truncate">{user?.email}</p>
            </div>
            <button
              onClick={signOut}
              className="rounded-lg p-1.5 text-white/60 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
              title="تسجيل الخروج"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
