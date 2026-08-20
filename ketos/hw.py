"""Pick how many float64 qubits this machine can hold."""

from __future__ import annotations

import os
import subprocess
import sys

TARGET_QUBITS = 28
MAX_QUBITS = 28
MIN_QUBITS = 2
BYTES_PER_AMP = 16  # complex128 = 2 × float64
OS_HEADROOM = 4 << 30
GPU_HEADROOM = 512 << 20


def sv_bytes(n: int) -> int:
    return BYTES_PER_AMP * (1 << int(n))


def ram_bytes() -> int:
    try:
        with open("/proc/meminfo", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            class _M(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            info = _M()
            info.dwLength = ctypes.sizeof(_M)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(info)):
                return int(info.ullTotalPhys)
        except Exception:
            pass
    try:
        out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
        return int(out.strip())
    except Exception:
        pass
    return 8 << 30


def probe_cuda() -> dict | None:
    try:
        from .cuda_api import probe

        return probe()
    except Exception:
        return None


def choose_n(target: int = TARGET_QUBITS) -> int:
    env = os.environ.get("KETOS_QUBITS")
    if env:
        return max(MIN_QUBITS, min(MAX_QUBITS, int(env)))
    target = max(MIN_QUBITS, min(MAX_QUBITS, int(target)))
    force_cpu = os.environ.get("KETOS_DEVICE", "").lower() in ("cpu", "numpy", "host")
    if not force_cpu:
        gpu = probe_cuda()
        if gpu:
            for n in range(target, 7, -1):
                if int(gpu["vram"]) >= sv_bytes(n) + GPU_HEADROOM:
                    return n
    ram = ram_bytes()
    for n in range(target, 7, -1):
        need = int(sv_bytes(n) * 2.0) + OS_HEADROOM
        if ram >= need:
            return n
    return 8


def gib(n_bytes: int) -> str:
    n_bytes = int(n_bytes)
    if n_bytes >= (1 << 30):
        return f"{n_bytes / (1 << 30):.2f} GiB"
    if n_bytes >= (1 << 20):
        return f"{n_bytes / (1 << 20):.2f} MiB"
    return f"{n_bytes} B"
