"""Noiseless statevector. Little-endian, exact gates, F = 1. numpy float64."""

from __future__ import annotations

import math
import random
from typing import Callable, Iterable

import numpy as np

INV_SQRT2 = 1.0 / math.sqrt(2.0)
_CHUNK = 1 << 20


class Statevector:
    __slots__ = ("n", "re", "im", "rng")
    device = "cpu"

    def __init__(self, n: int, rng: Callable[[], float] | None = None) -> None:
        self.n = int(n)
        dim = 1 << self.n
        self.re = np.zeros(dim, dtype=np.float64)
        self.im = np.zeros(dim, dtype=np.float64)
        self.re[0] = 1.0
        self.rng = rng or random.random

    def clone(self) -> "Statevector":
        s = Statevector.__new__(Statevector)
        s.n = self.n
        s.re = self.re.copy()
        s.im = self.im.copy()
        s.rng = self.rng
        return s

    def _views(self, q: int):
        n = self.n
        shape = (1 << (n - 1 - q), 2, 1 << q)
        return self.re.reshape(shape), self.im.reshape(shape)

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
        re, im = self._views(q)
        ar = re[:, 0, :].copy()
        ai = im[:, 0, :].copy()
        br = re[:, 1, :].copy()
        bi = im[:, 1, :].copy()
        re[:, 0, :] = m00r * ar - m00i * ai + m01r * br - m01i * bi
        im[:, 0, :] = m00r * ai + m00i * ar + m01r * bi + m01i * br
        re[:, 1, :] = m10r * ar - m10i * ai + m11r * br - m11i * bi
        im[:, 1, :] = m10r * ai + m10i * ar + m11r * bi + m11i * br

    def h(self, q: int) -> None:
        self.apply2(q, INV_SQRT2, 0, INV_SQRT2, 0, INV_SQRT2, 0, -INV_SQRT2, 0)

    def x(self, q: int) -> None:
        re, im = self._views(q)
        re[:, [0, 1], :] = re[:, [1, 0], :]
        im[:, [0, 1], :] = im[:, [1, 0], :]

    def y(self, q: int) -> None:
        self.apply2(q, 0, 0, 0, -1, 0, 1, 0, 0)

    def z(self, q: int) -> None:
        re, im = self._views(q)
        re[:, 1, :] *= -1.0
        im[:, 1, :] *= -1.0

    def s(self, q: int) -> None:
        self.apply2(q, 1, 0, 0, 0, 0, 0, 0, 1)

    def sdg(self, q: int) -> None:
        self.apply2(q, 1, 0, 0, 0, 0, 0, 0, -1)

    def t(self, q: int) -> None:
        c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
        self.apply2(q, 1, 0, 0, 0, 0, 0, c, s)

    def tdg(self, q: int) -> None:
        c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
        self.apply2(q, 1, 0, 0, 0, 0, 0, c, -s)

    def rx(self, q: int, theta: float) -> None:
        c, s = math.cos(theta / 2), math.sin(theta / 2)
        self.apply2(q, c, 0, 0, -s, 0, -s, c, 0)

    def ry(self, q: int, theta: float) -> None:
        c, s = math.cos(theta / 2), math.sin(theta / 2)
        self.apply2(q, c, 0, -s, 0, s, 0, c, 0)

    def rz(self, q: int, theta: float) -> None:
        c, s = math.cos(theta / 2), math.sin(theta / 2)
        self.apply2(q, c, -s, 0, 0, 0, 0, c, s)

    def id(self, q: int) -> None:
        return None

    def _two_views(self, a: int, b: int):
        lo, hi = (a, b) if a < b else (b, a)
        shape = (
            1 << (self.n - 1 - hi),
            2,
            1 << (hi - lo - 1),
            2,
            1 << lo,
        )
        return self.re.reshape(shape), self.im.reshape(shape), lo, hi

    def cx(self, c: int, t: int) -> None:
        if c == t:
            return
        re, im, lo, hi = self._two_views(c, t)
        if c > t:
            tmp = re[:, 1, :, 0, :].copy()
            re[:, 1, :, 0, :] = re[:, 1, :, 1, :]
            re[:, 1, :, 1, :] = tmp
            tmp = im[:, 1, :, 0, :].copy()
            im[:, 1, :, 0, :] = im[:, 1, :, 1, :]
            im[:, 1, :, 1, :] = tmp
        else:
            tmp = re[:, 0, :, 1, :].copy()
            re[:, 0, :, 1, :] = re[:, 1, :, 1, :]
            re[:, 1, :, 1, :] = tmp
            tmp = im[:, 0, :, 1, :].copy()
            im[:, 0, :, 1, :] = im[:, 1, :, 1, :]
            im[:, 1, :, 1, :] = tmp

    def cz(self, c: int, t: int) -> None:
        if c == t:
            return
        re, im, _lo, _hi = self._two_views(c, t)
        re[:, 1, :, 1, :] *= -1.0
        im[:, 1, :, 1, :] *= -1.0

    def swap(self, a: int, b: int) -> None:
        if a != b:
            self.cx(a, b)
            self.cx(b, a)
            self.cx(a, b)

    def mcx(self, controls: Iterable[int], target: int) -> None:
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
        dim = self.re.size
        for base in range(0, dim, _CHUNK):
            end = min(base + _CHUNK, dim)
            idx = np.arange(base, end)
            sel = ((idx & mask) == mask) & ((idx & tb) == 0)
            i = idx[sel]
            if i.size == 0:
                continue
            j = i | tb
            self.re[i], self.re[j] = self.re[j].copy(), self.re[i].copy()
            self.im[i], self.im[j] = self.im[j].copy(), self.im[i].copy()

    def ccx(self, c0: int, c1: int, t: int) -> None:
        self.mcx([c0, c1], t)

    def apply_gate(self, name: str, q: int = 0, t: int = 0, extra: dict | None = None) -> None:
        extra = extra or {}
        n = name.lower()
        if n == "h":
            self.h(q)
        elif n == "x":
            self.x(q)
        elif n == "y":
            self.y(q)
        elif n == "z":
            self.z(q)
        elif n == "s":
            self.s(q)
        elif n == "sdg":
            self.sdg(q)
        elif n == "t":
            self.t(q)
        elif n == "tdg":
            self.tdg(q)
        elif n == "i":
            self.id(q)
        elif n == "rx":
            self.rx(q, float(extra.get("theta") or 0))
        elif n == "ry":
            self.ry(q, float(extra.get("theta") or 0))
        elif n == "rz":
            self.rz(q, float(extra.get("theta") or 0))
        elif n in ("cx", "cnot"):
            self.cx(q, t)
        elif n == "cz":
            self.cz(q, t)
        elif n == "swap":
            self.swap(q, t)
        elif n in ("ccx", "toffoli"):
            c2 = extra.get("c", None)
            if c2 is None:
                ctrls = extra.get("controls") or [0]
                c2 = ctrls[0]
            self.ccx(q, int(c2), t)
        elif n == "mcx":
            self.mcx(extra.get("controls") or [], q)
        else:
            raise ValueError(f"unknown gate {name}")

    def probabilities(self) -> np.ndarray:
        return self.re * self.re + self.im * self.im

    def measure(self, qargs: list[int] | None = None) -> dict:
        n = self.n
        t = qargs if qargs is not None else list(range(n))
        p = self.probabilities()
        r = float(self.rng())
        outcome = int(np.searchsorted(np.cumsum(p), r, side="left"))
        if outcome >= p.size:
            outcome = int(p.size - 1)
        bits = "".join(str((outcome >> q) & 1) for q in reversed(t))
        sv = self.clone()
        mask = 0
        for q in t:
            mask |= 1 << q
        keep = outcome & mask
        dim = sv.re.size
        for base in range(0, dim, _CHUNK):
            end = min(base + _CHUNK, dim)
            idx = np.arange(base, end)
            drop = (idx & mask) != keep
            re_sl = sv.re[base:end]
            im_sl = sv.im[base:end]
            re_sl[drop] = 0.0
            im_sl[drop] = 0.0
        norm = float(np.dot(sv.re, sv.re) + np.dot(sv.im, sv.im))
        scale = math.sqrt(norm) or 1.0
        sv.re /= scale
        sv.im /= scale
        return {"bits": bits, "sv": sv}

    def sample_counts(self, shots: int) -> dict[str, int]:
        p = self.probabilities()
        total = float(p.sum())
        if total <= 0:
            p = np.zeros_like(p)
            p[0] = 1.0
        else:
            p = p / total
        n = self.n
        idx = np.random.choice(p.size, size=int(shots), p=p)
        unique, counts = np.unique(idx, return_counts=True)
        return {format(int(i), f"0{n}b"): int(c) for i, c in zip(unique, counts)}

    def bloch(self, qs: list[int] | None = None) -> list[dict[str, float]]:
        n = self.n
        out: list[dict[str, float]] = []
        for q in (qs if qs is not None else range(n)):
            q = int(q)
            re, im = self._views(q)
            ar, ai = re[:, 0, :], im[:, 0, :]
            br, bi = re[:, 1, :], im[:, 1, :]
            p0 = float(np.sum(ar * ar + ai * ai))
            p1 = float(np.sum(br * br + bi * bi))
            xr = float(np.sum(ar * br + ai * bi))
            xi = float(np.sum(ar * bi - ai * br))
            x, y, z = 2 * xr, 2 * xi, p0 - p1
            purity = (1 + x * x + y * y + z * z) / 2
            out.append({"x": x, "y": y, "z": z, "purity": purity, "q": q})
        return out

    def top_amps(self, k: int = 8) -> list[dict]:
        n = self.n
        k = max(1, min(int(k), self.re.size))
        p = self.probabilities()
        if n >= 16:
            idx = np.argpartition(p, -k)[-k:]
            idx = idx[np.argsort(p[idx])[::-1]]
        else:
            idx = np.argsort(p)[::-1][:k]
        rows = []
        for i in idx:
            i = int(i)
            pi = float(p[i])
            if pi < 1e-12:
                continue
            rows.append({"bit": format(i, f"0{n}b"), "re": float(self.re[i]), "im": float(self.im[i]), "p": pi})
        return rows


def apply_circuit(n: int, gates: list[dict], rng: Callable[[], float] | None = None) -> Statevector:
    sv = Statevector(n, rng)
    for g in gates:
        sv.apply_gate(str(g.get("g", "")), int(g.get("q") or 0), int(g.get("t") or 0), g)
    return sv
