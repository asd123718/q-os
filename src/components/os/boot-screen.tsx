import { useEffect } from "react";
import { KetMark } from "./ket-mark";
import { useOs } from "@/lib/os/store";

export function BootScreen() {
  const log = useOs((s) => s.bootLog);
  const enterDesktop = useOs((s) => s.enterDesktop);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " " || e.key === "Escape") {
        e.preventDefault();
        enterDesktop();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [enterDesktop]);

  return (
    <button
      type="button"
      onClick={enterDesktop}
      className="flex h-dvh w-full cursor-pointer flex-col items-center justify-center bg-bg px-6 text-left text-fg"
    >
      <KetMark className="size-12 text-fg" />
      <h1 className="mt-6 font-sans text-3xl font-medium tracking-[-0.04em]">Ket OS</h1>
      <p className="mt-1 text-sm text-muted">精确态矢量 · 无噪声 · F = 1</p>
      <div className="mt-10 w-full max-w-md font-mono text-[12px] leading-6 text-muted">
        {log.map((line, i) => (
          <div key={`${i}-${line}`} className="truncate">
            <span className="text-subtle">{String(i + 1).padStart(2, "0")}  </span>
            {line}
          </div>
        ))}
      </div>
      <p className="mt-10 text-sm text-fg">点击任意处进入桌面</p>
      <p className="mt-1 text-xs text-subtle">或按 Enter</p>
    </button>
  );
}
