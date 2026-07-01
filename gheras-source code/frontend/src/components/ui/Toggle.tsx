import { cn } from "../../lib/cn";

interface ToggleProps {
  label?: string;
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function Toggle({ label, options, value, onChange, className }: ToggleProps) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      {label && <span className="text-sm font-medium text-gray-700">{label}</span>}
      <div className="inline-flex rounded-lg border border-gray-300 bg-gray-50 p-1">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={cn(
              "rounded-md px-4 py-2 text-sm font-medium transition-colors cursor-pointer",
              value === opt.value
                ? "bg-white text-sidebar shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
