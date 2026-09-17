import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

export default function FormInput({ className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        "w-full rounded-2xl border border-surface-light bg-surface px-4 py-2.5 text-sm text-text-primary outline-none transition-colors focus:border-accent",
        className
      )}
      {...props}
    />
  );
}