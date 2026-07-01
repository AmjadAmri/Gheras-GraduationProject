import { Link } from "react-router-dom";
import { cn } from "../lib/cn";
import { Avatar } from "./ui/Avatar";
import { Badge } from "./ui/Badge";
import { Pencil, Trash2, Sparkles } from "lucide-react";
import type { Child } from "../types/child";
import { formatAgeGroup } from "../lib/formatters";

interface ChildCardProps {
  child: Child;
  onDelete?: (id: number) => void;
  className?: string;
}

export function ChildCard({ child, onDelete, className }: ChildCardProps) {
  return (
    <div
      className={cn(
        "group rounded-xl bg-white border border-gray-100 shadow-sm overflow-hidden",
        className
      )}
    >
      <div className="bg-child-header px-4 py-4 flex items-center gap-3">
        <Avatar src={child.photo || child.avatarUrl} name={child.name} size="lg" />
        <div className="text-white">
          <h3 className="font-semibold text-lg">{child.name}</h3>
          <p className="text-sm text-white/80">
            {formatAgeGroup(child.ageGroup)} سنوات · {child.gender === "boy" ? "ولد" : "بنت"}
          </p>
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <Badge variant="success">{child.storiesCount} قصة</Badge>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to={`/create-story?childId=${child.id}`}
            className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white hover:bg-primary-hover transition-colors"
          >
            <Sparkles className="h-4 w-4" />
            إنشاء قصة
          </Link>
          <Link
            to={`/children/${child.id}/edit`}
            className="rounded-lg border border-gray-200 p-2 text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
          >
            <Pencil className="h-4 w-4" />
          </Link>
          {onDelete && (
            <button
              onClick={() => onDelete(child.id)}
              className="rounded-lg border border-gray-200 p-2 text-gray-500 hover:bg-red-50 hover:text-danger transition-colors cursor-pointer"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
