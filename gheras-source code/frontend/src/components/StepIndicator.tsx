import { cn } from "../lib/cn";
import { Check } from "lucide-react";

interface StepIndicatorProps {
  steps: string[];
  currentStep: number;
  className?: string;
}

export function StepIndicator({ steps, currentStep, className }: StepIndicatorProps) {
  return (
    <div className={cn("flex items-center justify-center gap-0", className)}>
      {steps.map((label, index) => {
        const isCompleted = index < currentStep;
        const isCurrent = index === currentStep;
        return (
          <div key={index} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold transition-colors",
                  isCompleted && "bg-primary text-white",
                  isCurrent && "bg-sidebar text-white",
                  !isCompleted && !isCurrent && "bg-gray-200 text-gray-500"
                )}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : index + 1}
              </div>
              <span
                className={cn(
                  "mt-1.5 text-xs font-medium",
                  isCurrent ? "text-sidebar" : "text-gray-500"
                )}
              >
                {label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "mx-3 h-0.5 w-12 rounded-full mt-[-1rem]",
                  index < currentStep ? "bg-primary" : "bg-gray-200"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
