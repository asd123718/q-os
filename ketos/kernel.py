"""Ket OS kernel — CPython + numpy float64 statevector, no noise, F = 1."""

from __future__ import annotations

import math
import sys
from typing import Any

import numpy as np

from .alu import run_alu
from .hw import TARGET_QUBITS, choose_n, gib, sv_bytes
from .sv import Statevector, apply_circuit

N_SYS = TARGET_QUBITS
FIDELITY = 1.0
ENGINE = "ket.statevector"
PY_VER = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
NP_VER = np.__version__

def djb2(text: str) -> int:
    h = 5381
    for ch in text:
        h = ((h << 5) + h + ord(ch)) & 255
    return h


def pack(sv: Statevector, extra: dict | None = None, shots: int | None = None, light: bool = False) -> dict[str, Any]:
    extra = extra or {}
    n = sv.n
    if light:
        qs = [q for q in (0, 1, 4, 5) if q < n]
        bloch = sv.bloch(qs)
        entropy = 0.0
        occupancy = 0
        amps: list[dict] = []
        counts = None
    else:
        bloch = sv.bloch()
        p = sv.probabilities()
        occupancy = int(np.count_nonzero(p > 1e-6))
        pp = p[p > 1e-12]
        entropy = float(-(pp * np.log2(pp)).sum()) if pp.size else 0.0
        amps = sv.top_amps()
        counts = sv.sample_counts(shots) if shots else None
    out: dict[str, Any] = {
        "n": n,
        "bloch": bloch,
        "amps": amps,
        "counts": counts,
        "fidelity": FIDELITY,
        "noise": False,
        "backend": extra.get("backend", "cpython-sv"),
        "version": extra.get("version", PY_VER),
        "engine": ENGINE,
        "entropy": entropy,
        "occupancy": occupancy,
        "dtype": "float64",
        "sv_bytes": sv_bytes(n),
        "numpy": NP_VER,
    }
    out.update(extra)
    return out


class Kernel:
    def __init__(self, n: int | None = None) -> None:
        self.n = int(n) if n is not None else choose_n()
        self.sv = Statevector(self.n)
        self.boot_bits: str | None = None
        self.log: list[str] = []
        self.syscalls = 0
        self.backend_label = f"cpython-{PY_VER}"
        self.version = PY_VER

    def status(self) -> dict[str, Any]:
        return {
            "backend": self.backend_label,
            "version": self.version,
            "engine": ENGINE,
            "n_qubits": self.n,
            "allocated": self.n,
            "target_qubits": TARGET_QUBITS,
            "fidelity": FIDELITY,
            "noise": False,
            "shots_model": "exact Born sampling",
            "boot_bits": self.boot_bits,
            "syscalls": self.syscalls,
            "log": self.log[-24:],
            "python": sys.version.split()[0],
            "executable": sys.executable,
            "dtype": "float64",
            "sv_bytes": sv_bytes(self.n),
            "numpy": NP_VER,
        }

    def handle(self, req: dict[str, Any]) -> dict[str, Any]:
        op = req.get("op")
        args = req.get("args") or {}
        if op in ("ping", "status"):
            result = self.status()
        elif op == "boot":
            result = self.boot()
        elif op == "register":
            result = {**pack(self.sv, light=False), **self.status()}
        elif op == "reset":
            self.sv = Statevector(self.n)
            self.log.append("reset ⊗ |0⟩")
            result = {**pack(self.sv, light=self.n > 20), **self.status()}
        elif op == "run":
            result = self.run(args)
        elif op == "syscall":
            result = self.syscall(str(args.get("name") or ""), args)
        elif op == "teleport":
            result = self.teleport(args)
        elif op == "grover":
            result = self.grover(args)
        elif op == "add":
            result = self.add(args)
        elif op == "alu":
            result = self.alu(args)
        elif op == "encode":
            result = self.encode(args)
        elif op == "idle":
            result = self.idle()
        else:
            raise ValueError(f"unknown op {op}")
        if "syscalls" not in result:
            result = {**self.status(), **result}
        return result

    def boot(self) -> dict[str, Any]:
        self.log = []
        self.syscalls = 0
        self.log.append(f"{self.backend_label} · numpy {NP_VER} · float64 · noise=off")
        self.log.append(f"allocate {self.n} qubits in |0⟩^{self.n}  ({gib(sv_bytes(self.n))})")
        self.sv = Statevector(self.n)
        ghz = apply_circuit(4, [{"g": "h", "q": 0}, {"g": "cx", "q": 0, "t": 1}, {"g": "cx", "q": 1, "t": 2}, {"g": "cx", "q": 2, "t": 3}])
        ghz_probs = {a["bit"]: a["p"] for a in ghz.top_amps(8)}
        self.log.append("self-test GHZ₄  H·CX·CX·CX")
        bits = ghz.measure()["bits"]
        self.boot_bits = bits
        self.log.append(f"measure GHZ → |{bits}⟩")
        leaked = [k for k in ghz_probs if k not in ("0000", "1111")]
        if leaked:
            raise RuntimeError("GHZ self-test leaked amplitude")
        self.log.append("GHZ support = {0000, 1111} · F=1.000")
        self.sv = apply_circuit(self.n, [{"g": "h", "q": 0}, {"g": "cx", "q": 0, "t": 1}])
        self.log.append("kernel heartbeat: Bell(q0,q1)")
        self.log.append("scheduler / fs / rng banks ready")
        self.log.append(f"interpreter {sys.executable}")
        return {**pack(self.sv, light=self.n > 20), **self.status(), "ghz_probs": ghz_probs, "boot_ok": True}

    def idle(self) -> dict[str, Any]:
        if self.n > 4:
            self.sv.rx(4, math.pi / 16)
        if self.n > 5:
            self.sv.rz(5, math.pi / 8)
        return {**pack(self.sv, light=self.n > 20), **self.status(), "idle": True}

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        self.syscalls += 1
        n = int(args.get("n") or 2)
        gates = list(args.get("gates") or [])
        shots = int(args.get("shots") or 0)
        commit = bool(args.get("commit"))
        sv = apply_circuit(n, gates)
        if commit:
            if n == self.n:
                self.sv = sv
            self.log.append(f"commit {n}q circuit ({len(gates)} gates)")
        extra: dict[str, Any] = {
            "qasm": "\n".join(f"{g.get('g')} {' '.join(str(x) for x in (g.get('q'), g.get('t')) if x is not None)}" for g in gates),
            "gate_count": len(gates),
            "backend": self.backend_label,
            "version": self.version,
        }
        if shots:
            m = sv.measure()
            extra["collapsed"] = m["bits"]
            extra["collapsed_bloch"] = m["sv"].bloch()
        return pack(sv, extra, shots or None)

    def syscall(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        self.syscalls += 1
        if name == "exec":
            return self.sys_exec(int(args.get("app_id") or 0))
        if name == "schedule":
            return self.sys_schedule(list(args.get("pids") or []))
        if name == "rng":
            return self.sys_rng(int(args.get("n") or 8))
        if name == "fingerprint":
            return self.sys_fingerprint(str(args.get("text") or ""))
        raise ValueError(f"unknown syscall {name}")

    def sys_exec(self, app_id: int) -> dict[str, Any]:
        app_id %= 16
        gates = []
        for i, b in enumerate(format(app_id, "04b")[::-1]):
            if b == "1":
                gates.append({"g": "x", "q": i})
        bits = apply_circuit(4, gates).measure()["bits"]
        got = int(bits, 2)
        self.log.append(f"SYS_EXEC encode |{bits}⟩ measure → app {got}")
        return {"name": "exec", "app_id": got, "bits": bits, "n": 4, "fidelity": FIDELITY, "deterministic": got == app_id, "backend": self.backend_label}

    def sys_schedule(self, pids: list[int]) -> dict[str, Any]:
        uniq = sorted({int(p) % 16 for p in (pids or [0, 1, 2, 3])})
        sv = Statevector(4)
        sv.re[0] = 0.0
        a = 1.0 / math.sqrt(len(uniq))
        for p in uniq:
            sv.re[p] = a
        probabilities = {format(p, "04b"): a * a for p in uniq}
        bits = sv.measure()["bits"]
        pid = int(bits, 2)
        self.log.append(f"SYS_SCHED superposition {{{','.join(map(str, uniq))}}} → PID {pid}")
        return {"name": "schedule", "pids": uniq, "probabilities": probabilities, "pid": pid, "bits": bits, "fidelity": FIDELITY, "backend": self.backend_label}

    def sys_rng(self, n: int) -> dict[str, Any]:
        n = max(1, min(12, n))
        bits = apply_circuit(n, [{"g": "h", "q": q} for q in range(n)]).measure()["bits"]
        value = int(bits, 2)
        self.log.append(f"SYS_RNG H^{n} measure → {bits}")
        return {"name": "rng", "n": n, "bits": bits, "value": value, "fidelity": FIDELITY, "backend": self.backend_label}

    def sys_fingerprint(self, text: str) -> dict[str, Any]:
        h = djb2(text)
        gates = []
        for i, b in enumerate(format(h, "08b")[::-1]):
            if b == "1":
                gates.append({"g": "x", "q": i})
        bits = apply_circuit(8, gates).measure()["bits"]
        got = int(bits, 2)
        self.log.append(f"SYS_FINGERPRINT |{bits}⟩")
        return {"name": "fingerprint", "bits": bits, "value": got, "expected": h, "match": got == h, "fidelity": FIDELITY, "backend": self.backend_label}

    def teleport(self, args: dict[str, Any]) -> dict[str, Any]:
        self.syscalls += 1
        theta = float(args.get("theta") if args.get("theta") is not None else 0.7)
        phi = float(args.get("phi") if args.get("phi") is not None else 0.4)
        alice = apply_circuit(1, [{"g": "ry", "q": 0, "theta": theta}, {"g": "rz", "q": 0, "theta": phi}]).bloch()[0]
        sv = apply_circuit(
            3,
            [
                {"g": "ry", "q": 0, "theta": theta},
                {"g": "rz", "q": 0, "theta": phi},
                {"g": "h", "q": 1},
                {"g": "cx", "q": 1, "t": 2},
                {"g": "cx", "q": 0, "t": 1},
                {"g": "h", "q": 0},
            ],
        )
        m = sv.measure([0, 1])
        sv = m["sv"]
        m0 = int(m["bits"][-1])
        m1 = int(m["bits"][-2])
        if m1 == 1:
            sv.x(2)
        if m0 == 1:
            sv.z(2)
        bob = sv.bloch()[2]
        fid = 0.5 * (1 + alice["x"] * bob["x"] + alice["y"] * bob["y"] + alice["z"] * bob["z"])
        self.log.append(f"SYS_TELEPORT m={m['bits']} F={fid:.6f}")
        return {
            "theta": theta,
            "phi": phi,
            "alice": alice,
            "bob": bob,
            "alice_bits": m["bits"],
            "m0": m0,
            "m1": m1,
            "fidelity": fid,
            "backend": self.backend_label,
            "version": self.version,
            "noise": False,
        }

    def grover(self, args: dict[str, Any]) -> dict[str, Any]:
        self.syscalls += 1
        n = max(2, min(4, int(args.get("n") or 3)))
        marked = int(args.get("marked") or 5) % (1 << n)
        default_iters = max(1, int(math.floor((math.pi / 4) * math.sqrt(1 << n))))
        iters = int(args.get("iters") or default_iters)
        gates: list[dict[str, Any]] = [{"g": "h", "q": q} for q in range(n)]

        def oracle() -> None:
            bits = format(marked, f"0{n}b")[::-1]
            for i, b in enumerate(bits):
                if b == "0":
                    gates.append({"g": "x", "q": i})
            gates.append({"g": "h", "q": n - 1})
            gates.append({"g": "mcx", "q": n - 1, "controls": list(range(n - 1))})
            gates.append({"g": "h", "q": n - 1})
            for i, b in enumerate(bits):
                if b == "0":
                    gates.append({"g": "x", "q": i})

        def diffusion() -> None:
            for q in range(n):
                gates.append({"g": "h", "q": q})
            for q in range(n):
                gates.append({"g": "x", "q": q})
            gates.append({"g": "h", "q": n - 1})
            gates.append({"g": "mcx", "q": n - 1, "controls": list(range(n - 1))})
            gates.append({"g": "h", "q": n - 1})
            for q in range(n):
                gates.append({"g": "x", "q": q})
            for q in range(n):
                gates.append({"g": "h", "q": q})

        history = []
        sv = apply_circuit(n, list(gates))
        history.append({"iter": 0, "p_marked": float(sv.re[marked] ** 2 + sv.im[marked] ** 2)})
        for k in range(iters):
            oracle()
            diffusion()
            sv = apply_circuit(n, list(gates))
            history.append({"iter": k + 1, "p_marked": float(sv.re[marked] ** 2 + sv.im[marked] ** 2)})
        bits = sv.measure()["bits"]
        found = int(bits, 2)
        self.log.append(f"SYS_GROVER n={n} marked={marked} → {found}")
        return pack(
            sv,
            {
                "n": n,
                "marked": marked,
                "marked_bits": format(marked, f"0{n}b"),
                "iters": iters,
                "history": history,
                "found": found,
                "found_bits": bits,
                "success": found == marked,
                "backend": self.backend_label,
                "version": self.version,
            },
            int(args.get("shots") or 512),
        )

    def add(self, args: dict[str, Any]) -> dict[str, Any]:
        self.syscalls += 1
        a = int(args.get("a") or 0) & 0b11
        b = int(args.get("b") or 0) & 0b11
        gates: list[dict[str, Any]] = []
        if a & 1:
            gates.append({"g": "x", "q": 0})
        if a & 2:
            gates.append({"g": "x", "q": 1})
        if b & 1:
            gates.append({"g": "x", "q": 2})
        if b & 2:
            gates.append({"g": "x", "q": 3})
        gates += [
            {"g": "cx", "q": 0, "t": 4},
            {"g": "cx", "q": 2, "t": 4},
            {"g": "ccx", "q": 0, "c": 2, "t": 6},
            {"g": "cx", "q": 1, "t": 5},
            {"g": "cx", "q": 3, "t": 5},
            {"g": "cx", "q": 6, "t": 5},
            {"g": "ccx", "q": 1, "c": 3, "t": 7},
            {"g": "ccx", "q": 1, "c": 6, "t": 7},
            {"g": "ccx", "q": 3, "c": 6, "t": 7},
        ]
        bits = apply_circuit(8, gates).measure()["bits"]
        s0 = int(bits[3])
        s1 = int(bits[2])
        cout = int(bits[0])
        total = s0 + (s1 << 1) + (cout << 2)
        self.log.append(f"SYS_ADD {a}+{b} → {total}")
        return {
            "a": a,
            "b": b,
            "sum": total,
            "expected": a + b,
            "match": total == a + b,
            "bits": bits,
            "s0": s0,
            "s1": s1,
            "cout": cout,
            "fidelity": FIDELITY,
            "backend": self.backend_label,
            "version": self.version,
            "noise": False,
        }

    def alu(self, args: dict[str, Any]) -> dict[str, Any]:
        self.syscalls += 1
        op = str(args.get("alu_op") or args.get("op") or "add")
        out = run_alu(op, int(args.get("a") or 0), int(args.get("b") or 0), int(args.get("width") or 8))
        self.log.append(f"SYS_ALU {out['alu_op']} {out['a']},{out['b']} → {out['result']}")
        return {**out, "fidelity": FIDELITY, "backend": self.backend_label, "version": self.version, "noise": False}

    def encode(self, args: dict[str, Any]) -> dict[str, Any]:
        self.syscalls += 1
        raw = "".join(c for c in str(args.get("bits") or "0") if c in "01")[:12] or "0"
        gates = [{"g": "x", "q": i} for i, b in enumerate(raw[::-1]) if b == "1"]
        bits = apply_circuit(len(raw), gates).measure()["bits"]
        self.log.append(f"SYS_ENCODE |{bits}⟩")
        return {"n": len(raw), "bits": bits, "requested": raw, "match": bits == raw, "fidelity": FIDELITY, "backend": self.backend_label}


_ENGINE: Kernel | None = None


def get_engine() -> Kernel:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Kernel()
        _ENGINE.boot()
    return _ENGINE
