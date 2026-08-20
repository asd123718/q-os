export type AppId =
  | "register"
  | "circuit"
  | "terminal"
  | "files"
  | "scheduler"
  | "teleport"
  | "grover"
  | "calc"
  | "logic"
  | "taskmgr"
  | "about";

export type AppDef = {
  id: AppId;
  pid: number;
  title: string;
  subtitle: string;
  w: number;
  h: number;
};

export const APP_CATALOG: AppDef[] = [
  { id: "register", pid: 1, title: "量子寄存器", subtitle: "Bloch 球 · 振幅", w: 680, h: 500 },
  { id: "circuit", pid: 2, title: "线路实验室", subtitle: "编排门并测量", w: 820, h: 560 },
  { id: "terminal", pid: 3, title: "终端", subtitle: "ket 壳层", w: 640, h: 440 },
  { id: "files", pid: 4, title: "文件系统", subtitle: "读写删 · 量子指纹", w: 720, h: 520 },
  { id: "scheduler", pid: 5, title: "调度器", subtitle: "叠加态抽签", w: 580, h: 460 },
  { id: "teleport", pid: 6, title: "量子传送", subtitle: "Bell 对 · F=1", w: 600, h: 500 },
  { id: "grover", pid: 7, title: "Grover 搜索", subtitle: "振幅放大", w: 640, h: 500 },
  { id: "calc", pid: 8, title: "计算器", subtitle: "24-bit 量子 ALU", w: 360, h: 560 },
  { id: "logic", pid: 10, title: "逻辑器", subtitle: "门 · 移位 · 计数", w: 640, h: 540 },
  { id: "taskmgr", pid: 11, title: "任务管理器", subtitle: "Q-CPU · 内存 · 比特", w: 720, h: 540 },
  { id: "about", pid: 9, title: "关于本机", subtitle: "Qiskit 内核", w: 520, h: 460 },
];

export function appById(id: AppId) {
  return APP_CATALOG.find((a) => a.id === id)!;
}
