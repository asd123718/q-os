import { useEffect } from "react";
import { useOs } from "@/lib/os/store";
import { KetMark } from "../ket-mark";

export function AboutApp() {
  const backend = useOs((s) => s.backend);
  const kernel = useOs((s) => s.kernel);
  useEffect(() => {
    void kernel("status");
  }, [kernel]);
  const rows = [
    ["后端", `${backend?.backend ?? "—"} ${backend?.version ?? ""}`],
    ["引擎", String(backend?.engine ?? "qiskit.quantum_info.Statevector")],
    ["量子比特", String(backend?.n_qubits ?? 8)],
    ["噪声模型", backend?.noise ? "有" : "无"],
    ["门保真度", `${((backend?.fidelity ?? 1) * 100).toFixed(1)}%`],
    ["抽样", String(backend?.shots_model ?? "exact Born sampling")],
    ["启动向量", backend?.boot_bits ? `|${backend.boot_bits}⟩` : "—"],
    ["系统调用", String(backend?.syscalls ?? 0)],
  ];
  return (
    <div className="flex h-full flex-col gap-5 p-6">
      <div className="flex items-center gap-3">
        <KetMark className="size-10" />
        <div>
          <h2 className="text-lg font-medium tracking-[-0.03em]">Ket OS</h2>
          <p className="text-xs text-muted">量子操作系统 · 每个 syscall 都是一条线路</p>
        </div>
      </div>
      <dl className="grid grid-cols-[120px_1fr] gap-y-2 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-muted">{k}</dt>
            <dd className="font-mono text-[12px]">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="text-xs leading-5 text-muted">
        内核使用 Qiskit 的精确态矢量演化。没有退相干，没有读出误差。打开应用、调度进程、写文件、做算术，全部先编码到量子比特再测量。
      </p>
    </div>
  );
}
