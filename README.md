# Ket OS

双击就能跑的量子操作系统。Clone 之后**不用安装 Node、不用 pip、不用任何依赖**。

## 启动

| 系统 | 怎么开 |
|---|---|
| Windows | 双击 `start.bat` 或 `KetOS.html` |
| macOS | 双击 `Start.command` 或 `KetOS.html` |
| Linux | 双击 `start.sh` 或 `KetOS.html` |

全部计算在浏览器里用无噪声态矢量完成（门保真度 100%）。计算器、逻辑器、文件指纹、Grover、传送都走量子线路测量。

## 源码

```
KetOS.html                 可双击的整包（内置引擎 + UI）
quantum/kernel.py          可选 Qiskit 内核
src/lib/quantum/           浏览器态矢量 + 24-bit ALU
src/components/os/         桌面与应用
```
