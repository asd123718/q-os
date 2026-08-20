"""Noiseless statevector. Little-endian, exact gates, F = 1."""

from __future__ import annotations

import math
import random
from array import array
from typing import Callable, Iterable

INV_SQRT2 = 1.0 / math.sqrt(2.0)


class Statevector:
    __slots__ = ("n", "re", "im", "rng")

    def __init__(self, n: int, rng: Callable[[], float] | None = None) -> None:
        self.n = int(n)
        dim = 1 << self.n
        self.re = array("d", [0.0]) * dim
        self.im = array("d", [0.0]) * dim
        self.re[0] = 1.0
        self.rng = rng or random.random

    def clone(self) -> "Statevector":
        s = Statevector(self.n, self.rng)
        s.re = array("d", self.re)
        s.im = array("d", self.im)
        return s

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
        bit = 1 << q
        re = self.re
        im = self.im
        dim = len(re)
        for i in range(dim):
            if i & bit:
                continue
            j = i | bit
            ar, ai = re[i], im[i]
            br, bi = re[j], im[j]
            re[i] = m00r * ar - m00i * ai + m01r * br - m01i * bi
            im[i] = m00r * ai + m00i * ar + m01r * bi + m01i * br
            re[j] = m10r * ar - m10i * ai + m11r * br - m11i * bi
            im[j] = m10r * ai + m10i * ar + m11r * bi + m11i * br

    def h(self, q: int) -> None:
        self.apply2(q, INV_SQRT2, 0, INV_SQRT2, 0, INV_SQRT2, 0, -INV_SQRT2, 0)

    def x(self, q: int) -> None:
        self.apply2(q, 0, 0, 1, 0, 1, 0, 0, 0)

    def y(self, q: int) -> None:
        self.apply2(q, 0, 0, 0, -1, 0, 1, 0, 0)

    def z(self, q: int) -> None:
        self.apply2(q, 1, 0, 0, 0, 0, 0, -1, 0)

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

    def cx(self, c: int, t: int) -> None:
        cb, tb = 1 << c, 1 << t
        re, im = self.re, self.im
        dim = len(re)
        for i in range(dim):
            if (i & cb) and not (i & tb):
                j = i | tb
                re[i], re[j] = re[j], re[i]
                im[i], im[j] = im[j], im[i]

    def cz(self, c: int, t: int) -> None:
        mask = (1 << c) | (1 << t)
        re, im = self.re, self.im
        for i in range(len(re)):
            if (i & mask) == mask:
                re[i] = -re[i]
                im[i] = -im[i]

    def swap(self, a: int, b: int) -> None:
        if a != b:
            self.cx(a, b)
            self.cx(b, a)
            self.cx(a, b)

    def mcx(self, controls: Iterable[int], target: int) -> None:
        mask = 0
        for c in controls:
            mask |= 1 << int(c)
        tb = 1 << target
        re, im = self.re, self.im
        dim = len(re)
        for i in range(dim):
            if (i & mask) == mask and not (i & tb):
                j = i | tb
                re[i], re[j] = re[j], re[i]
                im[i], im[j] = im[j], im[i]

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

    def probabilities(self) -> array:
        re, im = self.re, self.im
        out = array("d", [0.0]) * len(re)
        for i, (a, b) in enumerate(zip(re, im)):
            out[i] = a * a + b * b
        return out

    def measure(self, qargs: list[int] | None = None) -> dict:
        n = self.n
        t = qargs if qargs is not None else list(range(n))
        probs = self.probabilities()
        r = self.rng()
        outcome = len(probs) - 1
        for i, p in enumerate(probs):
            r -= p
            if r <= 0:
                outcome = i
                break
        bits = "".join(str((outcome >> q) & 1) for q in reversed(t))
        sv = self.clone()
        mask = 0
        for q in t:
            mask |= 1 << q
        keep = outcome & mask
        norm = 0.0
        for i in range(len(sv.re)):
            if (i & mask) != keep:
                sv.re[i] = 0.0
                sv.im[i] = 0.0
            else:
                norm += sv.re[i] ** 2 + sv.im[i] ** 2
        scale = math.sqrt(norm) or 1.0
        for i in range(len(sv.re)):
            sv.re[i] /= scale
            sv.im[i] /= scale
        return {"bits": bits, "sv": sv}

    def sample_counts(self, shots: int) -> dict[str, int]:
        probs = self.probabilities()
        n = self.n
        counts: dict[str, int] = {}
        for _ in range(int(shots)):
            r = self.rng()
            outcome = len(probs) - 1
            for i, p in enumerate(probs):
                r -= p
                if r <= 0:
                    outcome = i
                    break
            key = format(outcome, f"0{n}b")
            counts[key] = counts.get(key, 0) + 1
        return counts

    def bloch(self) -> list[dict[str, float]]:
        n = self.n
        out: list[dict[str, float]] = []
        re, im = self.re, self.im
        dim = len(re)
        for q in range(n):
            bit = 1 << q
            p0 = p1 = xr = xi = 0.0
            for i in range(dim):
                if i & bit:
                    continue
                j = i | bit
                ar, ai = re[i], im[i]
                br, bi = re[j], im[j]
                p0 += ar * ar + ai * ai
                p1 += br * br + bi * bi
                xr += ar * br + ai * bi
                xi += ar * bi - ai * br
            x, y, z = 2 * xr, 2 * xi, p0 - p1
            purity = (1 + x * x + y * y + z * z) / 2
            out.append({"x": x, "y": y, "z": z, "purity": purity})
        return out

    def top_amps(self, k: int = 8) -> list[dict]:
        n = self.n
        rows = []
        for i, (a, b) in enumerate(zip(self.re, self.im)):
            p = a * a + b * b
            if p < 1e-12:
                continue
            rows.append({"bit": format(i, f"0{n}b"), "re": a, "im": b, "p": p})
        rows.sort(key=lambda r: r["p"], reverse=True)
        return rows[:k]


def apply_circuit(n: int, gates: list[dict], rng: Callable[[], float] | None = None) -> Statevector:
    sv = Statevector(n, rng)
    for g in gates:
        sv.apply_gate(str(g.get("g", "")), int(g.get("q") or 0), int(g.get("t") or 0), g)
    return sv
