# Ket OS

量子操作系统桌面。clone 之后**不用装 Node / npm / Python / 任何依赖**，内核已经打进 `KetOS.html`。

精确态矢量模拟，无噪声，门保真度 F = 1。

## 启动

clone 完直接双击：

| 系统 | 双击 |
| --- | --- |
| Windows | `START.bat` |
| macOS | `START.command`（若提示无权限：`chmod +x START.command`） |
| Linux | `START.sh` |

也可以直接用浏览器打开 `KetOS.html`。不需要本地服务器。

```bash
git clone https://github.com/asd123718/q-os.git
cd q-os
```

## 功能

- 多窗口桌面：拖动、缩放、最大化 / 还原
- 24-bit 量子 ALU 计算器（涟波全加器）
- 逻辑器、文件系统（8-qubit 指纹）、电路、寄存器
- Grover、量子传送
- 任务管理器：每秒刷新 Q-CPU / Q-MEM / 8 个内核量子比特

## 说明

这是一份**自包含发布包**。量子引擎、桌面和应用都在 `KetOS.html` 里，浏览器就是运行时。
