import { cn } from "../lib/cn";
import { Check } from "lucide-react";

interface SelectableGridItem {
  id: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
  previewUrl?: string;
}

interface SelectableGridProps {
  items: SelectableGridItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  columns?: 2 | 3;
  className?: string;
}

export function SelectableGrid({
  items,
  selectedId,
  onSelect,
  columns = 3,
  className,
}: SelectableGridProps) {
  return (
    <div
      className={cn(
        "grid gap-4",
        columns === 2 ? "grid-cols-2" : "grid-cols-2 md:grid-cols-3",
        className
      )}
    >
      {items.map((item) => {
        const isSelected = item.id === selectedId;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onSelect(item.id)}
            className={cn(
              "relative flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-center transition-all cursor-pointer",
              isSelected
                ? "border-primary bg-emerald-50 shadow-sm"
                : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
            )}
          >
            {isSelected && (
              <div className="absolute top-2 end-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-white">
                <Check className="h-3 w-3" />
              </div>
            )}
            {item.previewUrl ? (
              <img
                src={item.previewUrl}
                alt={item.label}
                className="h-20 w-full rounded-lg object-cover"
              />
            ) : (
              item.icon && (
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-sidebar">
                  {item.icon}
                </div>
              )
            )}
            <span className="text-sm font-semibold text-gray-900">{item.label}</span>
            {item.description && (
              <span className="text-xs text-gray-500 line-clamp-2">{item.description}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
