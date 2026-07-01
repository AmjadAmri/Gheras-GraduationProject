import { cn } from "../../lib/cn";
import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
  children: ReactNode;
  fullWidth?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  fullWidth = false,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer",
        {
          "bg-primary text-white hover:bg-primary-hover focus:ring-primary":
            variant === "primary",
          "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-300":
            variant === "secondary",
          "bg-danger text-white hover:bg-danger-hover focus:ring-danger":
            variant === "danger",
          "bg-transparent text-gray-600 hover:bg-gray-100 focus:ring-gray-300":
            variant === "ghost",
          "border-2 border-primary text-primary hover:bg-emerald-50 focus:ring-primary":
            variant === "outline",
        },
        {
          "px-3 py-1.5 text-sm": size === "sm",
          "px-4 py-2 text-sm": size === "md",
          "px-6 py-3 text-base": size === "lg",
        },
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
