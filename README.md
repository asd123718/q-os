# Ket OS

量子操作系统。clone 之后**不用装 Python / Node / npm / Qiskit**。

仓库里带着 **CPython 3.12.14** 便携解释器（Windows / macOS / Linux）。双击 START，解释器自己解开，量子内核在 Python 里跑，浏览器只负责画桌面。

精确态矢量，无噪声，门保真度 F = 1。

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

第一次会把对应平台的 CPython 解压到 `runtime/py/`（大约半分钟），然后打开 `http://127.0.0.1:8080/`。

不要直接双击 HTML。没有 Python 后端就没有量子内核。

## 里面有什么

- `runtime/cpython-3.12.14-*.tar.gz` — 内置解释器（astral python-build-standalone）
- `ketos/` — 纯标准库态矢量引擎 + HTTP 服务（无 pip、无 numpy、无 Qiskit）
- `ui/` — 桌面外壳

## 功能

- 多窗口桌面
- 24-bit 量子 ALU（涟波全加器，CPython 逐位线路）
- 逻辑器、文件系统（8-qubit 指纹）、电路、寄存器
- Grover、量子传送
- 任务管理器：Q-CPU / Q-MEM / 8 个内核量子比特

## 说明

这是一份自包含发布包。解释器已经打进仓库，clone 下来就能跑。
