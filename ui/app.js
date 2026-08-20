"use strict";
const APPS = [
  {id:"calc",title:"计算器",color:"#ca5010",w:380,h:560},
  {id:"logic",title:"逻辑器",color:"#8764b8",w:640,h:520},
  {id:"files",title:"文件系统",color:"#f7b500",w:720,h:520},
  {id:"taskmgr",title:"任务管理器",color:"#0078d4",w:720,h:540},
  {id:"register",title:"量子寄存器",color:"#00b7c3",w:760,h:620},
  {id:"circuit",title:"线路实验室",color:"#4cc2ff",w:780,h:520},
  {id:"terminal",title:"终端",color:"#13a10e",w:640,h:420},
  {id:"grover",title:"Grover",color:"#9a5bd9",w:600,h:460},
  {id:"teleport",title:"量子传送",color:"#00cc6a",w:560,h:460},
  {id:"about",title:"关于本机",color:"#4cc2ff",w:520,h:560},
];
const GLYPH = {
  calc: '<rect x="7" y="4" width="18" height="24" rx="3"/><path d="M10 9h12M10 16h3v3h-3zM14.5 16h3v3h-3zM19 16h3v3h-3zM10 21h3v3h-3zM14.5 21h3v3h-3zM19 21h3v3h-3z"/>',
  logic: '<path d="M6 8h7c5 0 8 3.5 8 8s-3 8-8 8H6"/><path d="M6 12h4M6 20h4"/>',
  files: '<path d="M6 9h7l2 3h11v12H6z"/>',
  taskmgr: '<path d="M7 18h4v6H7zM14 12h4v12h-4zM21 8h4v16h-4z"/>',
  register: '<circle cx="16" cy="16" r="7"/><path d="M16 9v14M9 16h14"/>',
  circuit: '<circle cx="8" cy="10" r="2"/><circle cx="16" cy="10" r="2"/><circle cx="24" cy="22" r="2"/><path d="M10 10h4M16 12v6h8"/>',
  terminal: '<path d="M8 10l6 6-6 6M16 22h8"/>',
  grover: '<circle cx="14" cy="14" r="6"/><path d="M19 19l6 6"/>',
  teleport: '<circle cx="8" cy="16" r="3"/><circle cx="24" cy="16" r="3"/><path d="M11 16h10"/>',
  about: '<circle cx="16" cy="16" r="10"/><path d="M16 14v7M16 10.5v1.5"/>',
};
function tileIcon(id, size) {
  size = size || 32;
  return `<svg viewBox="0 0 32 32" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${GLYPH[id] || ""}</svg>`;
}
const files = [
  {id:"f1",name:"readme.txt",body:"Ket OS · CPython + numpy 态矢量内核 · float64 · 无噪声 · F=1\n系统寄存器默认 28 个双精度量子比特。"},
  {id:"f2",name:"bell.ket",body:"H 0\nCX 0 1"},
];
let windows = [];
let zTop = 10;
let focus = "";
let wid = 1;
let startOpen = false;
const meter = {cpu:0,mem:0,entropy:0,occ:0,sys:0};
let lastStatus = {backend:"cpython",version:"",log:[],n_qubits:28,python:"",dtype:"float64"};

function uiScale() {
  return Math.min(Math.max(window.innerWidth / 1920, 1), 2.15);
}
function applyScale() {
  document.documentElement.style.setProperty("--s", uiScale().toFixed(3));
}
applyScale();
let resizeTimer = 0;
window.addEventListener("resize", () => {
  applyScale();
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (document.querySelector(".desk")) paint();
  }, 80);
});

async function ket(op, args) {
  const r = await fetch("/api/ket", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({op, args: args || {}}),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || r.statusText);
  lastStatus = data;
  return data;
}

function fmtBytes(n) {
  n = Number(n || 0);
  if (n >= 1 << 30) return (n / (1 << 30)).toFixed(2) + " GiB";
  if (n >= 1 << 20) return (n / (1 << 20)).toFixed(2) + " MiB";
  return n ? n + " B" : "";
}

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

function drawBloch(canvas, b) {
  if (!canvas || !b) return;
  const ctx = canvas.getContext("2d");
  const r = 24, cx = 28, cy = 28;
  ctx.clearRect(0,0,56,56);
  ctx.strokeStyle = "#2a2e38";
  ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.stroke();
  ctx.strokeStyle = "#6a707a";
  ctx.beginPath(); ctx.ellipse(cx,cy,r,r*.35,0,0,Math.PI*2); ctx.stroke();
  const x = cx + b.x * r, y = cy - b.z * r;
  ctx.strokeStyle = "#e8eaee";
  ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(x,y); ctx.stroke();
  ctx.fillStyle = "#d5dae2";
  ctx.beginPath(); ctx.arc(x,y,3,0,Math.PI*2); ctx.fill();
}

async function openApp(id) {
  const meta = APPS.find(a => a.id === id);
  const s = uiScale();
  const bar = Math.round(52 * s) + 20;
  const w = {
    id: "w" + wid++,
    app: id,
    title: meta.title,
    x: Math.round(124 * s) + windows.length % 6 * Math.round(52 * s),
    y: Math.round(18 * s) + windows.length % 6 * Math.round(34 * s),
    w: Math.min(Math.round(meta.w * Math.min(s, 1.35)), innerWidth - Math.round(48 * s)),
    h: Math.min(Math.round(meta.h * Math.min(s, 1.25)), innerHeight - bar),
    z: ++zTop,
    min: false,
    max: false,
    enter: true,
  };
  windows.push(w);
  focus = w.id;
  startOpen = false;
  ket("syscall", {name:"exec", app_id: windows.length}).catch(()=>{});
  paint();
  requestAnimationFrame(() => { w.enter = false; });
}

function closeWin(id) {
  const w = windows.find(x => x.id === id);
  if (!w || w.leave) return;
  w.leave = true;
  paint();
  setTimeout(() => {
    windows = windows.filter(x => x.id !== id);
    focus = windows.filter(x => !x.min).at(-1)?.id || "";
    paint();
  }, 160);
}

let ticking = false;
function pulseUI() {
  const n = windows.filter(w => !w.min).length;
  meter.cpu = Math.min(1, 0.12 + 0.55 * (n / 6) + 0.22 * Math.min(1, meter.entropy / 4));
  meter.mem = Math.min(1, 0.10 + 0.10 * windows.length + 0.06 * files.length);
  const c = document.getElementById("clock");
  if (c) c.textContent = new Date().toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"});
  const cpu = document.getElementById("cpu");
  if (cpu) cpu.textContent = "CPU " + Math.round(meter.cpu * 100) + "%";
  const mem = document.getElementById("mem");
  if (mem) mem.textContent = "RAM " + Math.round(meter.mem * 100) + "%";
  const nq = document.getElementById("nq");
  if (nq) nq.textContent = (lastStatus.n_qubits || 28) + "q";
  const day = document.getElementById("clockday");
  if (day) day.textContent = new Date().toLocaleDateString();
  applyTaskmgrChrome();
}
function applyTaskmgrChrome() {
  const live = document.getElementById("taskmgr-live");
  if (!live) return;
  const cpuPct = live.querySelector("#qcpu-pct");
  const cpuBar = live.querySelector("#qcpu-bar");
  const memPct = live.querySelector("#qmem-pct");
  const memBar = live.querySelector("#qmem-bar");
  if (cpuPct) cpuPct.textContent = Math.round(meter.cpu * 100) + "%";
  if (cpuBar) cpuBar.style.width = (meter.cpu * 100) + "%";
  if (memPct) memPct.textContent = Math.round(meter.mem * 100) + "%";
  if (memBar) memBar.style.width = (meter.mem * 100) + "%";
  const rows = live.querySelector("#tm-rows");
  if (rows) {
    rows.innerHTML = windows.map(w => `<tr><td>${w.title}</td><td>${w.min?"sleep":w.id===focus?"focus":"run"}</td><td>${w.min?"1%":w.id===focus?Math.round(meter.cpu*100)+"%":Math.round(meter.cpu*40)+"%"}</td><td>${w.min?"3%":"12%"}</td></tr>`).join("");
  }
}
function applyTaskmgrQuantum(st) {
  const live = document.getElementById("taskmgr-live");
  if (!live) return;
  const set = (id, text) => { const n = live.querySelector("#"+id); if (n) n.textContent = text; };
  set("tm-entropy", meter.entropy.toFixed(3));
  set("tm-occ", String(meter.occ));
  set("tm-sys", String(meter.sys));
  set("tm-nq", String(st.n_qubits || 28));
  const meta = live.querySelector("#tm-meta");
  if (meta) {
    meta.textContent = `CPython ${st.python || st.version || ""} · numpy ${st.numpy || ""} · float64 · 无噪声`;
  }
  const bloch = st.bloch || [];
  live.querySelectorAll("canvas").forEach(c => drawBloch(c, bloch[Number(c.dataset.q)]));
}
async function quantumLoop() {
  if (ticking) {
    setTimeout(quantumLoop, 50);
    return;
  }
  ticking = true;
  try {
    const r = await ket("idle");
    meter.entropy = Number(r.entropy || 0);
    meter.occ = Number(r.occupancy || 0);
    meter.sys = Number(r.syscalls || 0);
    applyTaskmgrQuantum(r);
    pulseUI();
  } catch {}
  ticking = false;
  setTimeout(quantumLoop, 50);
}

function taskmgrView(st) {
  st = st || lastStatus;
  const bloch = st.bloch || [];
  const box = el("div", "pad");
  box.id = "taskmgr-live";
  box.innerHTML = `<div class="row"><div class="meter"><b>Q-CPU</b><span id="qcpu-pct">${Math.round(meter.cpu*100)}%</span><i id="qcpu-bar" style="width:${meter.cpu*100}%"></i></div>
    <div class="meter"><b>Q-MEM</b><span id="qmem-pct">${Math.round(meter.mem*100)}%</span><i id="qmem-bar" style="width:${meter.mem*100}%"></i></div></div>
    <div class="tm-stats">
      <div class="tm-stat"><small>熵</small><b id="tm-entropy">${meter.entropy.toFixed(3)}</b></div>
      <div class="tm-stat"><small>占用</small><b id="tm-occ">${meter.occ}</b></div>
      <div class="tm-stat"><small>系统调用</small><b id="tm-sys">${meter.sys}</b></div>
      <div class="tm-stat"><small>量子比特</small><b id="tm-nq">${st.n_qubits || 28}</b></div>
    </div>
    <p class="muted" id="tm-meta">CPython ${st.python || st.version || ""} · numpy ${st.numpy || ""} · float64 · 无噪声</p>
    <p class="muted">内核脉搏</p>
    <div class="qubits">${[0,1,2,3].map(i=>`<div class="q"><canvas width="56" height="56" data-q="${i}"></canvas><span>q${i}</span></div>`).join("")}</div>
    <table><thead><tr><th>窗口</th><th>状态</th><th>CPU</th><th>MEM</th></tr></thead><tbody id="tm-rows">${windows.map(w=>`<tr><td>${w.title}</td><td>${w.min?"sleep":w.id===focus?"focus":"run"}</td><td>${w.min?"1%":w.id===focus?Math.round(meter.cpu*100)+"%":Math.round(meter.cpu*40)+"%"}</td><td>${w.min?"3%":"12%"}</td></tr>`).join("")}</tbody></table>`;
  queueMicrotask(() => box.querySelectorAll("canvas").forEach(c => drawBloch(c, bloch[Number(c.dataset.q)])));
  return box;
}

function shortPath(p) {
  p = String(p || "");
  if (!p) return "—";
  const norm = p.replace(/\\/g, "/");
  const parts = norm.split("/").filter(Boolean);
  if (p.length <= 42 || parts.length <= 3) return p;
  return "…/" + parts.slice(-3).join("/");
}

function aboutView() {
  const n = lastStatus;
  const box = el("div", "pad about");
  const rows = [
    ["处理器", "CPython " + (n.python || n.version || "")],
    ["加速库", "numpy " + (n.numpy || "")],
    ["量子比特", (n.n_qubits ?? 28) + " × float64"],
    ["态矢量", fmtBytes(n.sv_bytes) || "—"],
    ["引擎", n.engine || "ket.statevector"],
    ["噪声", "无 · 门保真度 100%"],
    ["系统调用", String(n.syscalls ?? 0)],
  ];
  const exe = n.executable || "";
  const exeShort = shortPath(exe);
  box.innerHTML = `<div class="about-hero">
      <div class="logo">${tileIcon("about", 28)}</div>
      <div><h2>Ket OS</h2><p>量子内核在本机 CPython 里算，浏览器只画桌面。</p></div>
    </div>
    <div class="about-card">${rows.map(([k,v]) =>
      `<div class="kv"><span>${k}</span><b>${v ?? "—"}</b></div>`
    ).join("")}</div>
    <div class="about-card"><div class="kv path"><span>可执行文件</span><b title="${String(exe).replace(/"/g,"")}">${exeShort}</b></div></div>`;
  return box;
}

function calcView() {
  const box = el("div", "pad calc");
  let t = "0", acc = 0, op = null, fresh = true;
  const screen = el("div", "screen", "0");
  const bits = el("div", "muted mono", "0".repeat(8) + "…");
  const note = el("div", "muted", "24-bit 量子 ALU · CPython 涟波全加器");
  function show(v, b, msg) {
    t = String(v); screen.textContent = t; bits.textContent = "|" + b + "⟩"; note.textContent = msg;
  }
  function cur() { return Math.max(0, Math.min(16777215, Math.floor(Number(t) || 0))); }
  async function run(name, a, b) {
    const r = await ket("alu", {alu_op:name, a, b, width:24});
    const v = Number(r.result || 0);
    acc = v; fresh = true; op = null;
    show(v, String(r.bits || ""), `${name} ${a},${b} → ${v}  match=${r.match}  F=1  ${r.backend}`);
    return v;
  }
  const keys = el("div", "keys");
  ["C","⌫","±","÷","7","8","9","×","4","5","6","−","1","2","3","+","%","0","="].forEach(d => {
    const btn = el("button", d==="0"?"span2":d==="="?"eq":"", d);
    btn.onclick = async () => {
      if (/\d/.test(d)) {
        if (fresh || t === "0") t = d; else if (t.length < 8) t += d;
        fresh = false; screen.textContent = t; return;
      }
      if (d === "C") { t="0"; acc=0; op=null; fresh=true; show(0,"0".repeat(24),"清零"); return; }
      if (d === "⌫") { if (!fresh) { t = t.slice(0,-1)||"0"; screen.textContent = t; } return; }
      if (d === "±") { await run("neg", cur(), 0); return; }
      const map = {"+":"add","−":"sub","×":"mul","÷":"div","%":"mod"};
      if (map[d]) {
        const v = cur();
        if (op && !fresh) acc = await run(op, acc, v); else acc = v;
        op = map[d]; fresh = true; note.textContent = "op " + op; return;
      }
      if (d === "=" && op) await run(op, acc, cur());
    };
    keys.append(btn);
  });
  box.append(screen, bits, keys, note);
  return box;
}

function logicView() {
  const box = el("div", "pad");
  const a = Object.assign(el("input"), {value:"13", type:"number"});
  const b = Object.assign(el("input"), {value:"7", type:"number"});
  const out = el("pre", "mono muted", "选一个运算");
  const row = el("div", "row wrap");
  ["and","or","xor","nand","nor","not","shl","shr","rol","ror","inc","dec","neg"].forEach(name => {
    const btn = el("button", "", name);
    btn.onclick = async () => {
      const r = await ket("alu", {alu_op:name, a:Number(a.value), b:Number(b.value), width:8});
      out.textContent = `${r.alu_op} ${r.a},${r.b} → ${r.result}  |${r.bits}⟩  match=${r.match}  ${r.backend}`;
    };
    row.append(btn);
  });
  box.append(el("p","muted","8-bit 量子逻辑 · 每位一条 CPython 线路"), a, b, row, out);
  return box;
}

function filesView() {
  const box = el("div", "pad files");
  const list = el("div", "list");
  const ta = Object.assign(el("textarea"), {spellcheck:false});
  let cur = files[0];
  ta.value = cur.body;
  function render() {
    list.innerHTML = "";
    files.forEach(f => {
      const row = el("div", "frow" + (f.id===cur.id?" on":""));
      const open = el("button", "link", f.name);
      open.onclick = () => { cur = f; ta.value = f.body; render(); };
      const del = el("button", "danger", "删");
      del.onclick = e => {
        e.stopPropagation();
        const i = files.findIndex(x => x.id === f.id);
        if (i >= 0) files.splice(i, 1);
        cur = files[0] || {id:"n", name:"untitled.txt", body:""};
        if (!files.length) files.push(cur);
        ta.value = cur.body; render();
      };
      row.append(open, del); list.append(row);
    });
  }
  const write = el("button", "", "写入（量子指纹）");
  const status = el("p", "muted", "保存会把内容编码到 8 qubit 再测量");
  write.onclick = async () => {
    cur.body = ta.value;
    const r = await ket("syscall", {name:"fingerprint", text: cur.body});
    status.textContent = `fingerprint |${r.bits}⟩ match=${r.match} F=1  ${r.backend}`;
  };
  const neu = el("button", "", "新建");
  neu.onclick = () => { cur = {id:"f"+Date.now(), name:"note.txt", body:""}; files.unshift(cur); ta.value=""; render(); };
  const actions = el("div", "row"); actions.append(write, neu);
  ta.oninput = () => { cur.body = ta.value; };
  box.append(list, ta, actions, status); render();
  return box;
}

function registerView() {
  const box = el("div", "pad");
  const qs = el("div", "qubits");
  async function refresh(reset) {
    const r = await ket(reset ? "reset" : "register");
    const bloch = r.bloch || [];
    qs.innerHTML = bloch.map((b,i)=>`<div class="q"><canvas width="56" height="56"></canvas><span>q${b.q ?? i}</span></div>`).join("");
    qs.querySelectorAll("canvas").forEach((c,i) => drawBloch(c, bloch[i]));
  }
  const row = el("div", "row");
  const a = el("button", "", "刷新"); a.onclick = () => refresh(false);
  const b = el("button", "", "重置 |0⟩"); b.onclick = () => refresh(true);
  row.append(a, b);
  const nq = lastStatus.n_qubits || 28;
  box.append(el("p","muted",`系统寄存器 · ${nq} × float64 · 预览 q0–q${Math.min(7, nq-1)}`), row, qs);
  refresh(false);
  return box;
}

function circuitView() {
  const box = el("div", "pad");
  const n = 3, cols = 8;
  const grid = Array.from({length:n}, () => Array(cols).fill(null));
  let gate = "h";
  const pal = el("div", "row wrap");
  ["h","x","y","z","s","t","cx"].forEach(g => {
    const b = el("button", "", g.toUpperCase());
    b.onclick = () => { gate = g; };
    pal.append(b);
  });
  const board = el("div");
  const hist = el("div", "hist");
  function draw() {
    board.innerHTML = "";
    for (let q = 0; q < n; q++) {
      const row = el("div", "crow");
      row.append(el("span", "muted mono", "q"+q));
      for (let c = 0; c < cols; c++) {
        const cell = el("button", "cell", grid[q][c]?.toUpperCase() || "");
        cell.onclick = () => { grid[q][c] = gate; draw(); };
        row.append(cell);
      }
      board.append(row);
    }
  }
  const run = el("button", "eq", "运行 512 shots");
  run.onclick = async () => {
    const gates = [];
    for (let c = 0; c < cols; c++) for (let q = 0; q < n; q++) {
      const g = grid[q][c];
      if (g) gates.push(g === "cx" ? {g:"cx", q, t:(q+1)%n} : {g, q});
    }
    const r = await ket("run", {n, gates, shots:512});
    const entries = Object.entries(r.counts || {});
    const mx = Math.max(1, ...entries.map(([,v]) => v));
    hist.innerHTML = entries.map(([k,v]) => `<div class="bar"><i style="height:${Math.round(v/mx*80)}px"></i><span>${k}</span></div>`).join("");
  };
  draw();
  box.append(pal, board, run, hist);
  return box;
}

function termView() {
  const box = el("div", "pad term");
  const pre = el("pre", "mono");
  pre.textContent = "ket shell · help / boot / rng / add a b / alu op a b / status\nCPython backend\n";
  const inp = Object.assign(el("input"), {placeholder:">"});
  inp.onkeydown = async e => {
    if (e.key !== "Enter") return;
    const line = inp.value.trim(); inp.value = "";
    const [cmd, ...rest] = line.split(/\s+/);
    let out = "";
    try {
      if (cmd === "help") out = "boot rng add alu status";
      else if (cmd === "boot") out = ((await ket("boot")).log || []).join("\n");
      else if (cmd === "rng") out = JSON.stringify(await ket("syscall", {name:"rng", n:8}));
      else if (cmd === "add") {
        const r = await ket("add", {a:Number(rest[0]), b:Number(rest[1])});
        out = `${r.a}+${r.b}=${r.sum} match=${r.match}`;
      } else if (cmd === "alu") {
        const r = await ket("alu", {alu_op: rest[0]||"add", a:Number(rest[1]), b:Number(rest[2]), width:24});
        out = `${r.alu_op} → ${r.result}`;
      } else if (cmd === "status") out = JSON.stringify(await ket("status"));
      else out = "unknown";
    } catch (err) { out = String(err); }
    pre.textContent += "\n> " + line + "\n" + out;
    pre.scrollTop = pre.scrollHeight;
  };
  box.append(pre, inp);
  return box;
}

function groverView() {
  const box = el("div", "pad");
  const inp = Object.assign(el("input"), {type:"number", value:"5"});
  const out = el("pre", "mono muted");
  const btn = el("button", "eq", "搜索");
  btn.onclick = async () => {
    const r = await ket("grover", {n:3, marked:Number(inp.value), shots:256});
    out.textContent = `marked ${r.marked} → found ${r.found} success=${r.success}\n` +
      (r.history||[]).map(h => `iter ${h.iter}  P=${Number(h.p_marked).toFixed(3)}`).join("\n");
  };
  box.append(el("p","muted","n=3 Grover 振幅放大 · CPython"), inp, btn, out);
  return box;
}

function teleportView() {
  const box = el("div", "pad");
  const out = el("pre", "mono muted");
  const btn = el("button", "eq", "传送");
  btn.onclick = async () => {
    const t = await ket("teleport", {theta:.7, phi:.4});
    out.textContent = `Alice (${t.alice?.x.toFixed(3)}, ${t.alice?.y.toFixed(3)}, ${t.alice?.z.toFixed(3)})
Bob   (${t.bob?.x.toFixed(3)}, ${t.bob?.y.toFixed(3)}, ${t.bob?.z.toFixed(3)})
m=${t.alice_bits}  F=${Number(t.fidelity).toFixed(6)}
${t.backend}`;
  };
  box.append(el("p","muted","Bell 对 · 无噪声 · CPython F=1"), btn, out);
  return box;
}

function appBody(id) {
  if (id === "taskmgr") return taskmgrView();
  if (id === "about") return aboutView();
  if (id === "calc") return calcView();
  if (id === "logic") return logicView();
  if (id === "files") return filesView();
  if (id === "register") return registerView();
  if (id === "circuit") return circuitView();
  if (id === "terminal") return termView();
  if (id === "grover") return groverView();
  if (id === "teleport") return teleportView();
  return el("div", "pad", id);
}

function winEl(w) {
  const s = uiScale();
  const bar = Math.round(52 * s) + 20;
  const n = el("div", "win" + (w.id===focus?" focus":"") + (w.min?" min":"") + (w.enter?" enter":"") + (w.leave?" leave":""));
  n.style.left = (w.max?8:w.x)+"px";
  n.style.top = (w.max?8:w.y)+"px";
  n.style.width = (w.max?innerWidth-16:w.w)+"px";
  n.style.height = (w.max?innerHeight-bar:w.h)+"px";
  n.style.zIndex = String(w.z);
  if (w.min) n.style.display = "none";
  const title = el("div", "title");
  title.append(el("span", "", w.title));
  const btns = el("div", "wbtn");
  const mn = el("button", "cap", "–"); mn.onclick = e => { e.stopPropagation(); w.min = true; paint(); };
  const mx = el("button", "cap", "□"); mx.onclick = e => { e.stopPropagation(); w.max = !w.max; paint(); };
  const cl = el("button", "cap close", "×"); cl.onclick = e => { e.stopPropagation(); closeWin(w.id); };
  btns.append(mn, mx, cl); title.append(btns);
  let drag = null;
  title.onpointerdown = e => {
    if (w.max || e.target.closest(".wbtn")) return;
    focus = w.id; w.z = ++zTop;
    drag = {dx:e.clientX-w.x, dy:e.clientY-w.y};
    title.setPointerCapture(e.pointerId);
  };
  title.onpointermove = e => {
    if (!drag) return;
    w.x = e.clientX-drag.dx; w.y = Math.max(0, e.clientY-drag.dy);
    n.style.left = w.x+"px"; n.style.top = w.y+"px";
  };
  title.onpointerup = () => { drag = null; };
  const se = el("div", "se");
  let rs = null;
  se.onpointerdown = e => { e.stopPropagation(); rs = {x:e.clientX,y:e.clientY,w:w.w,h:w.h}; se.setPointerCapture(e.pointerId); };
  se.onpointermove = e => {
    if (!rs) return;
    w.w = Math.max(280, rs.w+e.clientX-rs.x); w.h = Math.max(180, rs.h+e.clientY-rs.y);
    n.style.width = w.w+"px"; n.style.height = w.h+"px";
  };
  se.onpointerup = () => { rs = null; };
  const body = el("div", "body");
  body.append(appBody(w.app));
  n.append(title, body, se);
  n.onmousedown = () => { if (focus !== w.id) { focus = w.id; w.z = ++zTop; paint(); } };
  return n;
}

function paint() {
  const root = document.getElementById("root");
  root.innerHTML = "";
  const first = !window.__deskReady;
  window.__deskReady = true;
  const desk = el("div", "desk" + (first ? " desk-in" : ""));
  desk.addEventListener("mousedown", e => {
    if (startOpen && !e.target.closest(".start") && !e.target.closest(".tb-start")) {
      startOpen = false;
      document.querySelector(".start")?.classList.remove("open");
    }
  });
  const nav = el("nav", "icons");
  APPS.forEach(a => {
    const b = el("button", "desk-icon");
    b.innerHTML = `<span class="tile" style="background:${a.color}">${tileIcon(a.id)}</span><span class="name">${a.title}</span>`;
    b.onclick = () => openApp(a.id);
    nav.append(b);
  });
  desk.append(nav);
  windows.forEach(w => desk.append(winEl(w)));

  const start = el("div", "start");
  start.innerHTML = `<h3>已固定</h3>`;
  const pins = el("div", "pins");
  APPS.forEach(a => {
    const p = el("button", "pin");
    p.innerHTML = `<span class="tile" style="background:${a.color}">${tileIcon(a.id)}</span><span class="name">${a.title}</span>`;
    p.onclick = () => openApp(a.id);
    pins.append(p);
  });
  start.append(pins);
  desk.append(start);
  if (startOpen) requestAnimationFrame(() => start.classList.add("open"));

  const dock = el("footer", "taskbar");
  const cluster = el("div", "tb-cluster");
  const ketBtn = el("button", "tb-start" + (startOpen ? " open" : ""));
  ketBtn.innerHTML = `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="square"><path d="M9 7v18M15 8l10 8-10 8"/></svg>`;
  ketBtn.title = "开始";
  ketBtn.onclick = () => { startOpen = !startOpen; paint(); };
  cluster.append(ketBtn);
  windows.forEach(w => {
    const meta = APPS.find(a => a.id === w.app);
    const b = el("button", "tb-btn" + (w.id===focus && !w.min ? " on" : ""));
    b.innerHTML = tileIcon(w.app, 20);
    b.style.color = meta ? meta.color : "#fff";
    b.title = w.title;
    b.onclick = () => {
      if (w.min) w.min = false;
      else if (w.id === focus) w.min = true;
      else { focus = w.id; w.z = ++zTop; }
      paint();
    };
    cluster.append(b);
  });
  dock.append(cluster);
  const now = new Date();
  const tray = el("div", "tray");
  tray.innerHTML = `<span id="cpu">CPU ${Math.round(meter.cpu*100)}%</span>
    <span id="mem">RAM ${Math.round(meter.mem*100)}%</span>
    <span id="nq">${lastStatus.n_qubits || 28}q</span>
    <div class="clock"><b id="clock">${now.toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"})}</b><small id="clockday">${now.toLocaleDateString()}</small></div>`;
  dock.append(tray);
  desk.append(dock);
  root.append(desk);
}

async function boot() {
  applyScale();
  const root = document.getElementById("root");
  try {
    const st = await ket("boot");
    const btn = el("button", "boot");
    btn.innerHTML = `<div class="mark">⟩</div><h1>Ket OS</h1>
      <p>CPython ${st.python || st.version}  ·  numpy ${st.numpy || ""}  ·  ${st.n_qubits} × float64  ·  F = 1</p>
      <pre>${(st.log||[]).join("\n")}</pre>
      <p>单击进入桌面</p>`;
    btn.onclick = () => {
      btn.classList.add("out");
      setTimeout(() => {
        window.__deskReady = false;
        root.innerHTML = "";
        paint();
        pulseUI();
        setInterval(pulseUI, 100);
        quantumLoop();
      }, 280);
    };
    root.append(btn);
  } catch (err) {
    root.innerHTML = `<div class="err">无法连接 CPython 内核：${err}<br>请用 START 脚本启动，不要直接打开 HTML。</div>`;
  }
}
boot();

