"""Smoke the CPython kernel. Exit 0 on success."""
from ketos.kernel import Kernel
from ketos.alu import run_alu

k = Kernel()
boot = k.boot()
assert boot["boot_ok"], boot
assert boot["backend"].startswith("cpython-")
print("boot", boot["backend"], boot["boot_bits"], "ok")

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

print("SELFTEST OK")
