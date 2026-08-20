"""Smoke the CPython + numpy kernel. Exit 0 on success."""

from ketos.kernel import Kernel
from ketos.alu import run_alu
from ketos.sv import Statevector, apply_circuit
from ketos.hw import choose_n, sv_bytes, TARGET_QUBITS

assert TARGET_QUBITS == 28
assert sv_bytes(28) == 16 * (1 << 28)
print("target", TARGET_QUBITS, "sv", sv_bytes(28), "choose_n(env-free path later)")

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
assert boot["backend"].startswith("cpython-")
assert boot["n_qubits"] == 8
assert boot["dtype"] == "float64"
print("boot", boot["backend"], "numpy", boot["numpy"], boot["boot_bits"], "ok")

alu = run_alu("add", 13, 7, 8)
assert alu["match"] and alu["result"] == 20, alu
print("add 13+7", alu["result"], "match", alu["match"])

sub = run_alu("sub", 20, 5, 8)
assert sub["match"] and sub["result"] == 15, sub
print("sub 20-5", sub["result"])

xor = run_alu("xor", 13, 7, 8)
assert xor["match"] and xor["result"] == (13 ^ 7), xor
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
print("idle entropy", round(idle["entropy"], 4), "occ", idle["occupancy"])

print("SELFTEST OK")
