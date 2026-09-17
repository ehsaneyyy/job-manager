import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export default function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-2xl bg-surface p-4 border border-surface-light/30", className)}>
      {children}
    </div>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="text-sm font-semibold text-text-muted">{children}</h2>;
}