"""NVIDIA CUDA driver API via ctypes. No toolkit, no pip — just nvcuda.dll / libcuda.so from the GPU driver."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

PTX_PATH = Path(__file__).with_name("kernels.ptx")

CUDA_SUCCESS = 0
CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR = 75
CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MINOR = 76
CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT = 16
CU_JIT_ERROR_LOG_BUFFER = 5
CU_JIT_ERROR_LOG_BUFFER_SIZE_BYTES = 6

_KERNELS = ("apply2", "pauli_x", "pauli_z", "cnot", "cphase", "mcx", "bloch")


class CudaError(RuntimeError):
    pass


def _load_lib():
    if sys.platform == "win32":
        return ctypes.WinDLL("nvcuda.dll")
    for name in ("libcuda.so.1", "libcuda.so"):
        try:
            return ctypes.CDLL(name)
        except OSError:
            continue
    raise CudaError("no NVIDIA driver library")


class _Api:
    def __init__(self, lib) -> None:
        self.lib = lib
        i = ctypes.c_int
        u = ctypes.c_uint
        p = ctypes.c_void_p
        ull = ctypes.c_uint64
        sz = ctypes.c_size_t

        def fn(name, restype=i, argtypes=()):
            f = getattr(lib, name)
            f.restype = restype
            f.argtypes = list(argtypes)
            return f

        self.cuInit = fn("cuInit", i, [u])
        self.cuDriverGetVersion = fn("cuDriverGetVersion", i, [ctypes.POINTER(i)])
        self.cuDeviceGetCount = fn("cuDeviceGetCount", i, [ctypes.POINTER(i)])
        self.cuDeviceGet = fn("cuDeviceGet", i, [ctypes.POINTER(i), i])
        self.cuDeviceGetName = fn("cuDeviceGetName", i, [ctypes.c_char_p, i, i])
        self.cuDeviceTotalMem_v2 = fn("cuDeviceTotalMem_v2", i, [ctypes.POINTER(sz), i])
        self.cuDeviceGetAttribute = fn("cuDeviceGetAttribute", i, [ctypes.POINTER(i), i, i])
        self.cuDevicePrimaryCtxRetain = fn("cuDevicePrimaryCtxRetain", i, [ctypes.POINTER(p), i])
        self.cuCtxSetCurrent = fn("cuCtxSetCurrent", i, [p])
        self.cuModuleLoadData = fn("cuModuleLoadData", i, [ctypes.POINTER(p), p])
        self.cuModuleLoadDataEx = fn(
            "cuModuleLoadDataEx",
            i,
            [ctypes.POINTER(p), p, u, ctypes.POINTER(i), ctypes.POINTER(p)],
        )
        self.cuModuleGetFunction = fn("cuModuleGetFunction", i, [ctypes.POINTER(p), p, ctypes.c_char_p])
        self.cuMemAlloc_v2 = fn("cuMemAlloc_v2", i, [ctypes.POINTER(ull), sz])
        self.cuMemFree_v2 = fn("cuMemFree_v2", i, [ull])
        self.cuMemsetD8_v2 = fn("cuMemsetD8_v2", i, [ull, ctypes.c_ubyte, sz])
        self.cuMemcpyHtoD_v2 = fn("cuMemcpyHtoD_v2", i, [ull, p, sz])
        self.cuMemcpyDtoH_v2 = fn("cuMemcpyDtoH_v2", i, [p, ull, sz])
        self.cuMemcpyDtoD_v2 = fn("cuMemcpyDtoD_v2", i, [ull, ull, sz])
        self.cuLaunchKernel = fn(
            "cuLaunchKernel",
            i,
            [p, u, u, u, u, u, u, u, p, ctypes.POINTER(p), ctypes.POINTER(p)],
        )
        self.cuCtxSynchronize = fn("cuCtxSynchronize", i, [])
        self.cuGetErrorString = fn("cuGetErrorString", i, [i, ctypes.POINTER(ctypes.c_char_p)])


def _err(api: _Api, code: int, what: str) -> None:
    if code == CUDA_SUCCESS:
        return
    msg = ctypes.c_char_p()
    try:
        api.cuGetErrorString(code, ctypes.byref(msg))
        detail = msg.value.decode("ascii", "replace") if msg.value else str(code)
    except Exception:
        detail = str(code)
    raise CudaError(f"{what}: {detail} ({code})")


class Session:
    def __init__(self) -> None:
        env = os.environ.get("KETOS_DEVICE", "").lower()
        if env in ("cpu", "numpy", "host"):
            raise CudaError("KETOS_DEVICE=cpu")
        lib = _load_lib()
        self.api = _Api(lib)
        _err(self.api, self.api.cuInit(0), "cuInit")
        n = ctypes.c_int()
        _err(self.api, self.api.cuDeviceGetCount(ctypes.byref(n)), "cuDeviceGetCount")
        if n.value < 1:
            raise CudaError("no CUDA device")
        self.device = ctypes.c_int()
        pick = 0
        best_vram = 0
        info = None
        for i in range(n.value):
            dev = ctypes.c_int()
            _err(self.api, self.api.cuDeviceGet(ctypes.byref(dev), i), "cuDeviceGet")
            meta = self._device_info(dev.value)
            if meta["vram"] > best_vram:
                best_vram = meta["vram"]
                pick = dev.value
                info = meta
        self.device = pick
        self.info = info or self._device_info(pick)
        ctx = ctypes.c_void_p()
        _err(self.api, self.api.cuDevicePrimaryCtxRetain(ctypes.byref(ctx), self.device), "cuDevicePrimaryCtxRetain")
        _err(self.api, self.api.cuCtxSetCurrent(ctx), "cuCtxSetCurrent")
        self.ctx = ctx
        self.mod = self._load_ptx()
        self.fns = {}
        for name in _KERNELS:
            fn = ctypes.c_void_p()
            _err(self.api, self.api.cuModuleGetFunction(ctypes.byref(fn), self.mod, name.encode()), name)
            self.fns[name] = fn
        self.partial = self.malloc(2048 * 4 * 8)

    def _device_info(self, dev: int) -> dict:
        name = ctypes.create_string_buffer(128)
        _err(self.api, self.api.cuDeviceGetName(name, 128, dev), "cuDeviceGetName")
        vram = ctypes.c_size_t()
        _err(self.api, self.api.cuDeviceTotalMem_v2(ctypes.byref(vram), dev), "cuDeviceTotalMem")
        major = ctypes.c_int()
        minor = ctypes.c_int()
        sm = ctypes.c_int()
        _err(self.api, self.api.cuDeviceGetAttribute(ctypes.byref(major), CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR, dev), "sm_major")
        _err(self.api, self.api.cuDeviceGetAttribute(ctypes.byref(minor), CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MINOR, dev), "sm_minor")
        _err(self.api, self.api.cuDeviceGetAttribute(ctypes.byref(sm), CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT, dev), "sm_count")
        ver = ctypes.c_int()
        self.api.cuDriverGetVersion(ctypes.byref(ver))
        return {
            "name": name.value.decode("utf-8", "replace"),
            "vram": int(vram.value),
            "sm": f"{major.value}.{minor.value}",
            "sms": int(sm.value),
            "driver": int(ver.value),
            "ordinal": int(dev),
        }

    def _load_ptx(self) -> ctypes.c_void_p:
        ptx = PTX_PATH.read_bytes()
        if not ptx.endswith(b"\0"):
            ptx += b"\0"
        image = ctypes.c_char_p(ptx)
        mod = ctypes.c_void_p()
        rc = self.api.cuModuleLoadData(ctypes.byref(mod), image)
        if rc == CUDA_SUCCESS:
            return mod
        log = ctypes.create_string_buffer(8192)
        logsz = ctypes.c_void_p(8192)
        opts = (ctypes.c_int * 2)(CU_JIT_ERROR_LOG_BUFFER, CU_JIT_ERROR_LOG_BUFFER_SIZE_BYTES)
        vals = (ctypes.c_void_p * 2)(ctypes.cast(log, ctypes.c_void_p), ctypes.cast(ctypes.pointer(ctypes.c_uint(8192)), ctypes.c_void_p))
        rc2 = self.api.cuModuleLoadDataEx(ctypes.byref(mod), image, 2, opts, vals)
        extra = log.value.decode("utf-8", "replace") if log.value else ""
        _err(self.api, rc2, f"cuModuleLoadDataEx {extra}")
        return mod

    def malloc(self, n: int) -> ctypes.c_uint64:
        p = ctypes.c_uint64()
        _err(self.api, self.api.cuMemAlloc_v2(ctypes.byref(p), n), "cuMemAlloc")
        return p

    def free(self, p: ctypes.c_uint64) -> None:
        if p and p.value:
            self.api.cuMemFree_v2(p.value)
            p.value = 0

    def zero(self, p: ctypes.c_uint64, n: int) -> None:
        _err(self.api, self.api.cuMemsetD8_v2(p.value, 0, n), "cuMemset")

    def htod(self, dst: ctypes.c_uint64, src, n: int) -> None:
        ptr = src if isinstance(src, ctypes.c_void_p) else ctypes.c_void_p(src)
        _err(self.api, self.api.cuMemcpyHtoD_v2(dst.value, ptr, n), "cuMemcpyHtoD")

    def dtoh(self, dst, src: ctypes.c_uint64, n: int) -> None:
        ptr = dst if isinstance(dst, ctypes.c_void_p) else ctypes.c_void_p(dst)
        _err(self.api, self.api.cuMemcpyDtoH_v2(ptr, src.value, n), "cuMemcpyDtoH")

    def dtod(self, dst: ctypes.c_uint64, src: ctypes.c_uint64, n: int) -> None:
        _err(self.api, self.api.cuMemcpyDtoD_v2(dst.value, src.value, n), "cuMemcpyDtoD")

    def set_f64(self, p: ctypes.c_uint64, index: int, value: float) -> None:
        v = ctypes.c_double(value)
        _err(self.api, self.api.cuMemcpyHtoD_v2(p.value + index * 8, ctypes.byref(v), 8), "set_f64")

    def launch(self, name: str, args: list, grid: int = 2048, block: int = 256) -> None:
        fn = self.fns[name]
        boxed = []
        for a in args:
            if isinstance(a, ctypes.c_uint64):
                boxed.append(a)
            elif isinstance(a, ctypes._SimpleCData):
                boxed.append(a)
            else:
                raise TypeError(type(a))
        arr = (ctypes.c_void_p * len(boxed))(*[ctypes.cast(ctypes.byref(a), ctypes.c_void_p) for a in boxed])
        _err(
            self.api,
            self.api.cuLaunchKernel(fn, int(grid), 1, 1, int(block), 1, 1, 0, None, arr, None),
            name,
        )
        _err(self.api, self.api.cuCtxSynchronize(), "sync")


_SESSION: Session | None = None
_FAILED: str | None = None


def session() -> Session:
    global _SESSION, _FAILED
    if _SESSION is not None:
        return _SESSION
    if _FAILED is not None:
        raise CudaError(_FAILED)
    try:
        _SESSION = Session()
        return _SESSION
    except Exception as exc:
        _FAILED = str(exc)
        raise


def probe() -> dict | None:
    try:
        return dict(session().info)
    except Exception:
        return None


def available() -> bool:
    return probe() is not None


def fits(n: int) -> bool:
    info = probe()
    if not info:
        return False
    need = (16 * (1 << int(n))) + (512 << 20)
    return int(info["vram"]) >= need
