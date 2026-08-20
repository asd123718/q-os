# Ket OS

量子操作系统。clone 之后**不用装 Python / Node / npm / Qiskit / CUDA Toolkit**。

仓库里带着 **CPython 3.12.14** 和 **numpy 2.5.2** 的离线轮子（Windows / macOS / Linux）。双击 START，解释器自己解开，numpy 本地装上。

有 NVIDIA GPU 时，**系统寄存器在显卡上跑**（CUDA 驱动 + 内置 PTX，float64 态矢量）。不需要安装 CUDA Toolkit / CuPy。没 GPU 就自动退回 numpy。

精确态矢量，**float64**，无噪声，门保真度 F = 1。

默认系统寄存器 **28 个双精度量子比特**（态矢量 4.00 GiB）。RTX 5080 16 GB GDDR7（约 960 GB/s）上这是显存带宽问题，不是算力问题。内存/显存不够时自动降档。也可以设 `KETOS_QUBITS=n` 或 `KETOS_DEVICE=cpu`。

## 启动

```bash
git clone https://github.com/asd123718/q-os.git
cd q-os
```

然后双击：

| 系统 | 双击 |
| --- | --- |
| Windows | `START.bat` |
| macOS | `START.command`（若提示无权限：`chmod +x START.command`） |
| Linux | `START.sh` |

第一次会把对应平台的 CPython 解压到 `runtime/py/`，再离线安装 numpy（大约半分钟），然后打开 `http://127.0.0.1:8080/`。

不要直接双击 HTML。没有 Python 后端就没有量子内核。

28 量子比特：GPU 约 4 GiB 显存；CPU 回退大约需要 8 GB 可用内存。

## 里面有什么

- `runtime/cpython-3.12.14-*.tar.gz` — 内置解释器（astral python-build-standalone）
- `runtime/wheels/numpy-2.5.2-cp312-*.whl` — 离线 numpy（小线路、ALU、无 GPU 时的回退）
- `ketos/kernels.ptx` — float64 态矢量门，CUDA 驱动 JIT（sm_70 → Blackwell sm_120）
- `ketos/` — 内核 + HTTP 服务（无 Qiskit、无联网 pip、无 CUDA Toolkit）
- `ui/` — 桌面外壳

## 功能

- 多窗口桌面
- 24-bit 量子 ALU（涟波全加器）
- 逻辑器、文件系统（8-qubit 指纹）、电路、寄存器
- Grover、量子传送
- 任务管理器：Q-CPU / Q-MEM / 内核脉搏
- 系统寄存器：最多 28 × float64，优先 CUDA

## 说明

这是一份自包含发布包。解释器和 numpy 已经打进仓库，clone 下来就能跑。GPU 只用已经装着的 NVIDIA 驱动。
