import { cn } from "../lib/cn";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color: string;
  bgColor: string;
  className?: string;
}

export function StatCard({ label, value, icon: Icon, color, bgColor, className }: StatCardProps) {
  return (
    <div className={cn("rounded-xl bg-white border border-gray-100 shadow-sm p-5", className)}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl", bgColor)}>
          <Icon className={cn("h-6 w-6", color)} />
        </div>
      </div>
    </div>
  );
}
