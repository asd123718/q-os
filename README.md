# Ket OS

用 Qiskit（无噪声、门保真度 100%）做后端的量子操作系统桌面。系统调用、ALU、文件系统指纹、调度都走精确态矢量测量。

仓库：https://github.com/asd123718/q-os

## 功能

- 桌面：多窗口、拖动、缩放、最大化/还原
- 24-bit 量子 ALU 计算器（涟波全加器）
- 逻辑器、文件系统、Grover、传送、终端
- 任务管理器：每秒刷新 Q-CPU / Q-MEM / 8 个内核量子比特

## 目录

```
quantum/kernel.py          Qiskit 内核
src/lib/quantum/           浏览器态矢量引擎 + ALU
src/lib/os/                窗口管理 / 文件 / 遥测
src/components/os/         桌面与应用 UI
```

## 运行

需要 Node 22+。可选：本机 Python + Qiskit 2（没有则自动用本地引擎）。

```bash
npm install
pip install -r quantum/requirements.txt
npm run dev
```

打开 http://localhost:8080

## 说明

内核寄存器是 8 qubit；计算器 ALU 是 24 位逐位全加器（每 bit 一个 4-qubit 电路）。
