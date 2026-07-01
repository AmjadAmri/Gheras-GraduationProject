import { cn } from "../../lib/cn";

interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
  color?: string;
}

export function ProgressBar({ value, max = 100, className, color }: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);
  return (
    <div className={cn("h-3 w-full rounded-full bg-gray-200 overflow-hidden", className)}>
      <div
        className={cn("h-full rounded-full transition-all duration-500 ease-out", color || "bg-primary")}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
