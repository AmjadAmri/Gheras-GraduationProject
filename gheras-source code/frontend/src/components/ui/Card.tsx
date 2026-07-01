import { cn } from "../../lib/cn";
import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: boolean;
}

export function Card({ children, padding = true, className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl bg-white border border-gray-100 shadow-sm",
        padding && "p-6",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
