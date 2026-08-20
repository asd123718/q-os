"""GPU statevector. Same gates as sv.Statevector, amplitudes live in VRAM as float64."""

from __future__ import annotations

import os
import random
from typing import Callable, Iterable

import numpy as np

from .sv import INV_SQRT2, Statevector

BLOCK = 256
MAX_GRID = 2048


def grid_for(npairs: int, block: int = BLOCK) -> int:
    return max(1, min(MAX_GRID, int((int(npairs) + block - 1) // block)))


class GpuStatevector(Statevector):
    device = "cuda"

    def __init__(self, n: int, rng: Callable[[], float] | None = None) -> None:
        from . import cuda_api

        self.n = int(n)
        self.rng = rng or random.random
        self._dim = 1 << self.n
        self._bytes = self._dim * 8
        self._dev = cuda_api.session()
        self._re = self._dev.malloc(self._bytes)
        self._im = self._dev.malloc(self._bytes)
        self._dev.zero(self._re, self._bytes)
        self._dev.zero(self._im, self._bytes)
        self._dev.set_f64(self._re, 0, 1.0)
        self.re = None  # type: ignore[assignment]
        self.im = None  # type: ignore[assignment]

    def __del__(self) -> None:
        try:
            dev = getattr(self, "_dev", None)
            if dev is None:
                return
            if getattr(self, "_re", None) is not None:
                dev.free(self._re)
            if getattr(self, "_im", None) is not None:
                dev.free(self._im)
        except Exception:
            pass

    def _npairs(self):
        import ctypes

        return ctypes.c_uint64(self._dim >> 1), ctypes.c_uint32

    def _launch_q(self, name: str, q: int, extra=()) -> None:
        import ctypes

        npairs = ctypes.c_uint64(self._dim >> 1)
        q32 = ctypes.c_uint32(int(q))
        grid = grid_for(self._dim >> 1)
        self._dev.launch(name, [self._re, self._im, npairs, q32, *extra], grid=grid, block=BLOCK)

    def apply2(
        self,
        q: int,
        m00r: float,
        m00i: float,
        m01r: float,
        m01i: float,
        m10r: float,
        m10i: float,
        m11r: float,
        m11i: float,
    ) -> None:
        import ctypes

        extra = [ctypes.c_double(x) for x in (m00r, m00i, m01r, m01i, m10r, m10i, m11r, m11i)]
        self._launch_q("apply2", q, extra)

    def x(self, q: int) -> None:
        self._launch_q("pauli_x", q)

    def z(self, q: int) -> None:
        self._launch_q("pauli_z", q)

    def cx(self, c: int, t: int) -> None:
        import ctypes

        if c == t:
            return
        npairs = ctypes.c_uint64(self._dim >> 1)
        t32 = ctypes.c_uint32(int(t))
        c32 = ctypes.c_uint32(int(c))
        grid = grid_for(self._dim >> 1)
        self._dev.launch("cnot", [self._re, self._im, npairs, t32, c32], grid=grid, block=BLOCK)

    def cz(self, c: int, t: int) -> None:
        import ctypes

        if c == t:
            return
        npairs = ctypes.c_uint64(self._dim >> 1)
        t32 = ctypes.c_uint32(int(t))
        c32 = ctypes.c_uint32(int(c))
        grid = grid_for(self._dim >> 1)
        self._dev.launch("cphase", [self._re, self._im, npairs, t32, c32], grid=grid, block=BLOCK)

    def mcx(self, controls: Iterable[int], target: int) -> None:
        import ctypes

        ctrls = [int(c) for c in controls]
        if not ctrls:
            self.x(target)
            return
        if len(ctrls) == 1:
            self.cx(ctrls[0], target)
            return
        mask = 0
        for c in ctrls:
            mask |= 1 << c
        tb = 1 << int(target)
        dim = ctypes.c_uint64(self._dim)
        m64 = ctypes.c_uint64(mask)
        tb64 = ctypes.c_uint64(tb)
        grid = grid_for(self._dim)
        self._dev.launch("mcx", [self._re, self._im, dim, m64, tb64], grid=grid, block=BLOCK)

    def clone(self) -> "GpuStatevector":
        s = GpuStatevector.__new__(GpuStatevector)
        s.n = self.n
        s.rng = self.rng
        s._dim = self._dim
        s._bytes = self._bytes
        s._dev = self._dev
        s._re = self._dev.malloc(self._bytes)
        s._im = self._dev.malloc(self._bytes)
        self._dev.dtod(s._re, self._re, self._bytes)
        self._dev.dtod(s._im, self._im, self._bytes)
        s.re = None  # type: ignore[assignment]
        s.im = None  # type: ignore[assignment]
        return s

    def _host(self) -> Statevector:
        sv = Statevector.__new__(Statevector)
        sv.n = self.n
        sv.rng = self.rng
        sv.re = np.empty(self._dim, dtype=np.float64)
        sv.im = np.empty(self._dim, dtype=np.float64)
        self._dev.dtoh(sv.re.ctypes.data, self._re, self._bytes)
        self._dev.dtoh(sv.im.ctypes.data, self._im, self._bytes)
        return sv

    def probabilities(self) -> np.ndarray:
        return self._host().probabilities()

    def measure(self, qargs: list[int] | None = None) -> dict:
        return self._host().measure(qargs)

    def sample_counts(self, shots: int) -> dict[str, int]:
        return self._host().sample_counts(shots)

    def top_amps(self, k: int = 8) -> list[dict]:
        return self._host().top_amps(k)

    def bloch(self, qs: list[int] | None = None) -> list[dict[str, float]]:
        import ctypes

        out: list[dict[str, float]] = []
        npairs_n = self._dim >> 1
        npairs = ctypes.c_uint64(npairs_n)
        grid = grid_for(npairs_n)
        buf = np.zeros((grid, 4), dtype=np.float64)
        for q in (qs if qs is not None else range(self.n)):
            q = int(q)
            q32 = ctypes.c_uint32(q)
            self._dev.zero(self._dev.partial, grid * 32)
            self._dev.launch(
                "bloch",
                [self._re, self._im, npairs, q32, self._dev.partial],
                grid=grid,
                block=BLOCK,
            )
            self._dev.dtoh(buf.ctypes.data, self._dev.partial, grid * 32)
            p0, p1, xr, xi = (float(x) for x in buf.sum(axis=0))
            x, y, z = 2 * xr, 2 * xi, p0 - p1
            purity = (1 + x * x + y * y + z * z) / 2
            out.append({"x": x, "y": y, "z": z, "purity": purity, "q": q})
        return out


def make_sv(n: int, rng: Callable[[], float] | None = None) -> Statevector:
    if os.environ.get("KETOS_DEVICE", "").lower() in ("cpu", "numpy", "host"):
        return Statevector(n, rng)
    try:
        from . import cuda_api

        if cuda_api.available() and cuda_api.fits(n):
            return GpuStatevector(n, rng)
    except Exception:
        pass
    return Statevector(n, rng)
