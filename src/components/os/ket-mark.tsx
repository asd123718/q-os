import { cn } from "@/lib/utils";

export function KetMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={cn("size-8", className)} aria-hidden="true">
      <path
        d="M8 6v20M14 7l12 9-12 9"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="square"
        strokeLinejoin="miter"
      />
    </svg>
  );
}
