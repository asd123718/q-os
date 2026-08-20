"""Smoke the CPython + numpy kernel. Exit 0 on success."""

from ketos.kernel import Kernel
from ketos.alu import run_alu
from ketos.sv import Statevector, apply_circuit
from ketos.hw import choose_n, sv_bytes, TARGET_QUBITS, probe_cuda
from ketos.sv_gpu import make_sv

assert TARGET_QUBITS == 28
assert sv_bytes(28) == 16 * (1 << 28)
print("target", TARGET_QUBITS, "sv", sv_bytes(28), "choose_n(env-free path later)")


def pair_ids(pair: int, q: int) -> tuple[int, int]:
    stride = 1 << q
    i0 = ((pair >> q) << (q + 1)) | (pair & (stride - 1))
    return i0, i0 + stride


# Pair indexing used by the CUDA kernels must match numpy reshape (2^{n-1-q}, 2, 2^q).
sv = Statevector(6)
for q in range(6):
    re, im = sv._views(q)
    npairs = 1 << 5
    for pair in range(npairs):
        i0, i1 = pair_ids(pair, q)
        hi, lo = pair >> q, pair & ((1 << q) - 1)
        assert abs(re[hi, 0, lo] - sv.re[i0]) < 1e-18
        assert abs(re[hi, 1, lo] - sv.re[i1]) < 1e-18
print("pair index matches numpy layout")

sv = Statevector(2)
sv.h(0)
sv.cx(0, 1)
p = sv.probabilities()
assert abs(float(p[0]) - 0.5) < 1e-12 and abs(float(p[3]) - 0.5) < 1e-12, p[:4]
print("bell ok")

sv = Statevector(3)
sv.x(0)
sv.x(1)
sv.ccx(0, 1, 2)
assert abs(float(sv.re[7]) - 1.0) < 1e-12, (sv.re[7], sv.im[7])
print("toffoli ok")

sv = apply_circuit(4, [{"g": "h", "q": 0}, {"g": "cx", "q": 0, "t": 3}])
p = sv.probabilities()
assert abs(float(p[0]) - 0.5) < 1e-12 and abs(float(p[9]) - 0.5) < 1e-12, p
print("cx high-bit ok")

sv = apply_circuit(3, [{"g": "h", "q": 2}, {"g": "cx", "q": 2, "t": 0}])
p = sv.probabilities()
assert abs(float(p[0]) - 0.5) < 1e-12 and abs(float(p[5]) - 0.5) < 1e-12, p
print("cx reverse ok")

k = Kernel(n=8)
boot = k.boot()
assert boot["boot_ok"], boot
assert boot["backend"].startswith("cpython-") or boot["backend"].startswith("cuda"), boot["backend"]
assert boot["n_qubits"] == 8
assert boot["dtype"] == "float64"
print("boot", boot["backend"], "device", boot.get("device"), "numpy", boot["numpy"], boot["boot_bits"], "ok")

alu = run_alu("add", 13, 7, 8)
assert alu["match"] and alu["result"] == 20, alu
print("add 13+7", alu["result"], "match", alu["match"])

sub = run_alu("sub", 20, 5, 8)
assert sub["match"] and sub["result"] == 15, sub
print("sub 20-5", sub["result"])

xor = run_alu("xor", 13, 7, 8)
assert xor["result"] == (13 ^ 7), xor
print("xor", xor["result"])

g = k.grover({"n": 3, "marked": 5, "shots": 64})
print("grover found", g["found"], "success", g["success"], "P", [round(h["p_marked"], 3) for h in g["history"]])

t = k.teleport({"theta": 0.7, "phi": 0.4})
print("teleport F", round(t["fidelity"], 6))
assert t["fidelity"] > 0.99, t

a = k.add({"a": 2, "b": 1})
print("ripple add", a)
assert a["match"], a

fp = k.sys_fingerprint("hello")
assert fp["match"], fp
print("fingerprint", fp["bits"])

idle = k.idle()
assert idle["n_qubits"] == 8
assert idle["entropy"] > 0.2, idle["entropy"]
assert len(idle["bloch"]) == 4, idle["bloch"]
ents = [round(k.idle()["entropy"], 4) for _ in range(12)]
assert len(set(ents)) >= 3, ents
assert max(ents) > 0.5, ents
print("idle entropy samples", ents)

reg = k.register()
assert len(reg["bloch"]) == 8
print("register bloch", len(reg["bloch"]))

info = probe_cuda()
print("cuda probe", info)
if info:
    from ketos.sv_gpu import GpuStatevector

    cpu = Statevector(6)
    gpu = GpuStatevector(6)
    for sv in (cpu, gpu):
        sv.h(0)
        sv.cx(0, 1)
        sv.rx(2, 0.7)
        sv.ry(3, 0.4)
        sv.x(4)
        sv.cz(0, 5)
        sv.ccx(1, 2, 4)
    cb = cpu.bloch()
    gb = gpu.bloch()
    for a, b in zip(cb, gb):
        for key in ("x", "y", "z"):
            assert abs(a[key] - b[key]) < 1e-9, (a, b)
    print("gpu vs cpu n=6 bloch match", info["name"], "sm", info["sm"], "vram", info["vram"])
else:
    print("cuda not present — numpy fallback (expected in this sandbox)")

print("SELFTEST OK")
