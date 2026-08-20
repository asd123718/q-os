"""Bit-serial quantum ALU. Every bit is a noiseless circuit (F = 1)."""

from __future__ import annotations

from typing import Any

from .sv import apply_circuit


def mask_w(width: int) -> int:
    width = max(1, min(32, width))
    return 0xFFFFFFFF if width == 32 else (1 << width) - 1


def bit_at(value: int, i: int) -> int:
    return (int(value) >> i) & 1


def shl_w(value: int, i: int, width: int) -> int:
    return (int(value) << i) & mask_w(width)


def to_bits(value: int, width: int) -> str:
    return "".join(str((value >> q) & 1) for q in range(width - 1, -1, -1))


def qbit(value: int, i: int) -> int:
    gates = []
    if bit_at(value, i):
        gates.append({"g": "x", "q": 0})
    return int(apply_circuit(1, gates).measure()["bits"][0])


def qread(value: int, n: int) -> dict[str, Any]:
    out = 0
    bits = ""
    for i in range(n - 1, -1, -1):
        b = qbit(value, i)
        bits += str(b)
        if b:
            out += 2**i
    return {"value": out, "bits": bits}


def qnot(value: int, n: int) -> dict[str, Any]:
    out = 0
    bits = ""
    for i in range(n - 1, -1, -1):
        gates = []
        if bit_at(value, i):
            gates.append({"g": "x", "q": 0})
        gates.append({"g": "x", "q": 0})
        b = int(apply_circuit(1, gates).measure()["bits"][0])
        bits += str(b)
        if b:
            out += 2**i
    return {"value": out, "bits": bits}


def full_adder(a: int, b: int, cin: int) -> dict[str, Any]:
    gates = []
    if a & 1:
        gates.append({"g": "x", "q": 0})
    if b & 1:
        gates.append({"g": "x", "q": 1})
    if cin & 1:
        gates.append({"g": "x", "q": 2})
    gates += [
        {"g": "ccx", "q": 0, "c": 1, "t": 3},
        {"g": "cx", "q": 0, "t": 1},
        {"g": "ccx", "q": 1, "c": 2, "t": 3},
        {"g": "cx", "q": 1, "t": 2},
    ]
    bits = apply_circuit(4, gates).measure()["bits"]
    return {"sum": int(bits[1]), "cout": int(bits[0]), "bits": bits}


def add_n(a: int, b: int, width: int, cin0: int = 0) -> dict[str, Any]:
    m = mask_w(width)
    a &= m
    b &= m
    cin = cin0
    value = 0
    steps = []
    for i in range(width):
        r = full_adder(bit_at(a, i), bit_at(b, i), cin)
        value += r["sum"] * (2**i)
        cin = r["cout"]
        steps.append({"i": i, "bits": r["bits"], "label": f"FA{i}", "sum": r["sum"], "cout": r["cout"]})
    return {"value": value, "carry": cin, "steps": steps}


def sub_n(a: int, b: int, width: int) -> dict[str, Any]:
    nb = qnot(b, width)
    r = add_n(a, nb["value"], width, 1)
    r["steps"] = [{"i": -1, "bits": nb["bits"], "label": "NOT"}, *r["steps"]]
    return r


def logic_bit(op: str, a: int, b: int) -> dict[str, Any]:
    gates = []
    if op == "not":
        if a & 1:
            gates.append({"g": "x", "q": 0})
        gates.append({"g": "x", "q": 0})
        bits = apply_circuit(1, gates).measure()["bits"]
        return {"bit": int(bits[0]), "bits": bits}
    if a & 1:
        gates.append({"g": "x", "q": 0})
    if b & 1:
        gates.append({"g": "x", "q": 1})
    if op == "xor":
        gates.append({"g": "cx", "q": 0, "t": 1})
        bits = apply_circuit(2, gates).measure()["bits"]
        return {"bit": int(bits[0]), "bits": bits}
    if op in ("and", "nand"):
        gates.append({"g": "ccx", "q": 0, "c": 1, "t": 2})
        if op == "nand":
            gates.append({"g": "x", "q": 2})
        bits = apply_circuit(3, gates).measure()["bits"]
        return {"bit": int(bits[0]), "bits": bits}
    if op in ("or", "nor"):
        gates += [{"g": "x", "q": 0}, {"g": "x", "q": 1}, {"g": "ccx", "q": 0, "c": 1, "t": 2}, {"g": "x", "q": 2}]
        if op == "nor":
            gates.append({"g": "x", "q": 2})
        bits = apply_circuit(3, gates).measure()["bits"]
        return {"bit": int(bits[0]), "bits": bits}
    raise ValueError(f"unknown logic {op}")


def logic_n(op: str, a: int, b: int, width: int) -> dict[str, Any]:
    value = 0
    steps = []
    for i in range(width):
        r = logic_bit(op, bit_at(a, i), bit_at(b, i))
        value |= r["bit"] << i
        steps.append({"i": i, "bits": r["bits"], "label": f"{op}{i}"})
    return {"value": value, "steps": steps}


def expected_of(op: str, a: int, b: int, width: int) -> int:
    m = mask_w(width)
    a &= m
    b &= m
    if op == "add":
        return (a + b) & m
    if op == "sub":
        return (a - b) & m
    if op == "mul":
        return (a * b) & m
    if op == "div":
        return 0 if b == 0 else (a // b) & m
    if op == "mod":
        return 0 if b == 0 else a % b
    if op == "and":
        return a & b
    if op == "or":
        return a | b
    if op == "xor":
        return a ^ b
    if op == "nand":
        return (~(a & b)) & m
    if op == "nor":
        return (~(a | b)) & m
    if op == "not":
        return (~a) & m
    if op == "shl":
        return (a << 1) & m
    if op == "shr":
        return (a >> 1) & m
    if op == "rol":
        return ((a << 1) | (a >> (width - 1))) & m
    if op == "ror":
        return ((a >> 1) | ((a & 1) << (width - 1))) & m
    if op == "inc":
        return (a + 1) & m
    if op == "dec":
        return (a - 1) & m
    if op == "neg":
        return ((~a) + 1) & m
    if op == "cmp":
        return 0 if a == b else (1 if a > b else m)
    return 0


def run_alu(op: str, raw_a: int, raw_b: int, width: int = 8) -> dict[str, Any]:
    width = max(2, min(32, int(width)))
    m = mask_w(width)
    a = int(max(0, int(raw_a))) & m
    b = int(max(0, int(raw_b))) & m
    op = op.lower()
    value = 0
    carry = 0
    steps: list[dict[str, Any]] = []

    if op == "add":
        r = add_n(a, b, width, 0)
        value, carry, steps = r["value"], r["carry"], r["steps"]
    elif op == "inc":
        r = add_n(a, 0, width, 1)
        value, carry, steps = r["value"], r["carry"], r["steps"]
    elif op == "sub":
        r = sub_n(a, b, width)
        value, carry, steps = r["value"], r["carry"], r["steps"]
    elif op == "dec":
        r = sub_n(a, 1, width)
        value, carry, steps = r["value"], r["carry"], r["steps"]
    elif op == "neg":
        r = sub_n(0, a, width)
        value, carry, steps = r["value"], r["carry"], r["steps"]
    elif op == "mul":
        acc = 0
        for i in range(width):
            bit = qbit(b, i)
            steps.append({"i": i, "bits": str(bit), "label": f"b[{i}]"})
            if bit:
                acc = add_n(acc, shl_w(a, i, width), width)["value"]
        carry = 1 if acc > m else 0
        value = acc & m
    elif op in ("div", "mod"):
        if b == 0:
            value = 0
            steps.append({"i": 0, "bits": "0", "label": "div0"})
        else:
            quot = 0
            rem = 0
            for i in range(width - 1, -1, -1):
                rem = rem * 2 + qbit(a, i)
                lo = rem & m
                hi = rem > m
                trial = sub_n(lo, b, width)
                ge = hi or trial["carry"] == 1
                if ge:
                    rem = (m + 1 + trial["value"]) if (hi and trial["carry"]) else trial["value"]
                    quot |= 1 << i
                last = trial["steps"][-1]["bits"] if trial["steps"] else ""
                steps.append({"i": i, "bits": last, "label": f"q{i}={1 if ge else 0}", "cout": trial["carry"]})
            value = (rem if op == "mod" else quot) & m
    elif op in ("and", "or", "xor", "nand", "nor", "not"):
        r = logic_n(op, a, b, width)
        value, steps = r["value"], r["steps"]
    elif op in ("shl", "shr", "rol", "ror"):
        src = qread(a, width)
        steps.append({"i": 0, "bits": src["bits"], "label": "read"})
        out = 0
        for i in range(width):
            bit = qbit(src["value"], i)
            if op == "shl" and i + 1 < width and bit:
                out |= 1 << (i + 1)
            if op == "shr" and i > 0 and bit:
                out |= 1 << (i - 1)
            if op == "rol" and bit:
                out |= 1 << ((i + 1) % width)
            if op == "ror" and bit:
                out |= 1 << ((i - 1 + width) % width)
        committed = qread(out, width)
        value = committed["value"]
        steps.append({"i": 1, "bits": committed["bits"], "label": "write"})
    elif op == "cmp":
        r = sub_n(a, b, width)
        carry = r["carry"]
        value = 0 if a == b else (1 if r["carry"] else m)
        steps = r["steps"]
    else:
        raise ValueError(f"unknown alu op {op}")

    expected = expected_of(op, a, b, width)
    return {
        "alu_op": op,
        "a": a,
        "b": b,
        "result": value,
        "expected": expected,
        "match": value == expected,
        "carry": carry,
        "zero": value == 0,
        "width": width,
        "bits": to_bits(value, width),
        "steps": steps[:24],
    }
