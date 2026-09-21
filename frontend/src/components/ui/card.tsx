import * as React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hover = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("card p-5", hover && "transition-colors hover:border-white/20", className)}
      {...props}
    />
  ),
);
Card.displayName = "Card";

export function CardLabel({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn("font-mono text-[11px] uppercase tracking-[0.08em] text-mist", className)}
      {...props}
    />
  );
}
