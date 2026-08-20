import { useState } from "react";
import { runAlu } from "@/lib/quantum/alu";
import { cn } from "@/lib/utils";

type Op = "add" | "sub" | "mul" | "div" | "mod";

const WIDTH = 24;
const MAX = (1 << WIDTH) - 1;

const KEYS: { label: string; kind: "digit" | "op" | "eq" | "fn"; op?: Op }[] = [
  { label: "C", kind: "fn" },
  { label: "⌫", kind: "fn" },
  { label: "±", kind: "fn" },
  { label: "÷", kind: "op", op: "div" },
  { label: "7", kind: "digit" },
  { label: "8", kind: "digit" },
  { label: "9", kind: "digit" },
  { label: "×", kind: "op", op: "mul" },
  { label: "4", kind: "digit" },
  { label: "5", kind: "digit" },
  { label: "6", kind: "digit" },
  { label: "−", kind: "op", op: "sub" },
  { label: "1", kind: "digit" },
  { label: "2", kind: "digit" },
  { label: "3", kind: "digit" },
  { label: "+", kind: "op", op: "add" },
  { label: "%", kind: "op", op: "mod" },
  { label: "0", kind: "digit" },
  { label: "=", kind: "eq" },
];

export function CalcApp() {
  const [display, setDisplay] = useState("0");
  const [acc, setAcc] = useState(0);
  const [pending, setPending] = useState<Op | null>(null);
  const [fresh, setFresh] = useState(true);
  const [bits, setBits] = useState("0".repeat(WIDTH));
  const [note, setNote] = useState(`${WIDTH}-bit 量子 ALU · 涟波全加器 · 最大 ${MAX}`);

  function parse() {
    const n = Math.floor(Number(display) || 0);
    return Math.max(0, Math.min(MAX, n));
  }

  function run(op: Op, a: number, b: number) {
    const r = runAlu(op, a, b, WIDTH);
    const n = Number(r.result ?? 0);
    setDisplay(String(n));
    setAcc(n);
    setBits(String(r.bits ?? "").padStart(WIDTH, "0"));
    const overflow = op === "mul" && a * b > MAX ? " 溢出截断" : "";
    setNote(`${op} ${a},${b} → ${n}${overflow}  match=${r.match}  F=1`);
    setFresh(true);
    return n;
  }

  function press(key: (typeof KEYS)[number]) {
    if (key.kind === "digit") {
      if (fresh || display === "0") setDisplay(key.label);
      else if (display.length < 8) setDisplay(display + key.label);
      setFresh(false);
      return;
    }
    if (key.label === "C") {
      setDisplay("0");
      setAcc(0);
      setPending(null);
      setFresh(true);
      setBits("0".repeat(WIDTH));
      setNote("清零");
      return;
    }
    if (key.label === "⌫") {
      if (fresh) return;
      const next = display.slice(0, -1);
      setDisplay(next.length ? next : "0");
      return;
    }
    if (key.label === "±") {
      const n = runAlu("neg", parse(), 0, WIDTH);
      const v = Number(n.result ?? 0);
      setDisplay(String(v));
      setBits(String(n.bits ?? "").padStart(WIDTH, "0"));
      setNote(`neg → ${v}`);
      setFresh(true);
      return;
    }
    if (key.kind === "op" && key.op) {
      const cur = parse();
      if (pending && !fresh) {
        const n = run(pending, acc, cur);
        setPending(key.op);
        setAcc(n);
        return;
      }
      setAcc(cur);
      setPending(key.op);
      setFresh(true);
      setNote(`op ${key.op} · ${WIDTH}q`);
      return;
    }
    if (key.kind === "eq") {
      if (!pending) return;
      run(pending, acc, parse());
      setPending(null);
    }
  }

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div className="rounded-md border border-border bg-elevated px-3 py-3">
        <div className="text-right font-mono text-4xl tabular-nums tracking-tight">{display}</div>
        <div className="mt-1 flex items-center justify-between gap-2 font-mono text-[11px] text-muted">
          <span className="min-w-0 truncate">|{bits}⟩</span>
          <span className="shrink-0">{pending ?? `${WIDTH}q`}</span>
        </div>
      </div>
      <div className="grid flex-1 grid-cols-4 gap-1.5">
        {KEYS.map((k) => (
          <button
            key={k.label}
            type="button"
            onClick={() => press(k)}
            className={cn(
              "min-h-11 rounded-sm text-sm font-medium",
              k.label === "0" && "col-span-2",
              k.kind === "eq" && "bg-primary text-primary-fg",
              k.kind === "op" && "bg-elevated text-fg",
              (k.kind === "digit" || k.kind === "fn") && "border border-border text-fg hover:bg-elevated",
              k.kind === "op" && "hover:opacity-90",
              k.kind === "eq" && "hover:opacity-90",
            )}
          >
            {k.label}
          </button>
        ))}
      </div>
      <p className="font-mono text-[11px] leading-4 text-muted">{note}</p>
    </div>
  );
}
