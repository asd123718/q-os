import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-sm border border-border bg-elevated px-3 text-sm text-fg outline-none placeholder:text-subtle focus-visible:ring-1 focus-visible:ring-ring",
        className,
      )}
      {...props}
    />
  );
}
