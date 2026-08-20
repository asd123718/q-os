"use strict";
const APPS = [
  {id:"calc",title:"计算器",w:360,h:560},
  {id:"logic",title:"逻辑器",w:640,h:520},
  {id:"files",title:"文件系统",w:720,h:520},
  {id:"taskmgr",title:"任务管理器",w:720,h:540},
  {id:"register",title:"量子寄存器",w:760,h:620},
  {id:"circuit",title:"线路实验室",w:780,h:520},
  {id:"terminal",title:"终端",w:640,h:420},
  {id:"grover",title:"Grover",w:600,h:460},
  {id:"teleport",title:"量子传送",w:560,h:460},
  {id:"about",title:"关于本机",w:560,h:460},
];
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
  const w = {
    id: "w" + wid++,
    app: id,
    title: meta.title,
    x: 56 + windows.length % 5 * 28,
    y: 36 + windows.length % 4 * 24,
    w: Math.min(meta.w, innerWidth - 24),
    h: Math.min(meta.h, innerHeight - 80),
    z: ++zTop,
    min: false,
    max: false,
  };
  windows.push(w);
  focus = w.id;
  startOpen = false;
  ket("syscall", {name:"exec", app_id: windows.length}).catch(()=>{});
  paint();
}

function closeWin(id) {
  windows = windows.filter(w => w.id !== id);
  focus = windows.at(-1)?.id || "";
  paint();
}

async function tick() {
  try {
    const r = await ket("idle");
    meter.entropy = Number(r.entropy || 0);
    meter.occ = Number(r.occupancy || 0);
    meter.sys = Number(r.syscalls || 0);
    const n = windows.filter(w => !w.min).length;
    meter.cpu = Math.min(1, .2 * Math.min(1, meter.entropy / 4) + .5 * (n / 6));
    meter.mem = Math.min(1, .08 * files.length + .12 * windows.length + meter.entropy / 8);
    const c = document.getElementById("clock");
    if (c) c.textContent = new Date().toLocaleTimeString();
    const cpu = document.getElementById("cpu");
    if (cpu) cpu.textContent = "cpu " + Math.round(meter.cpu * 100) + "%";
    const mem = document.getElementById("mem");
    if (mem) mem.textContent = "mem " + Math.round(meter.mem * 100) + "%";
    const live = document.getElementById("taskmgr-live");
    if (live) live.replaceWith(taskmgrView(r));
  } catch {}
}

function taskmgrView(st) {
  st = st || lastStatus;
  const bloch = st.bloch || [];
  const box = el("div", "pad");
  box.id = "taskmgr-live";
  box.innerHTML = `<div class="row"><div class="meter"><b>Q-CPU</b><span>${Math.round(meter.cpu*100)}%</span><i style="width:${meter.cpu*100}%"></i></div>
    <div class="meter"><b>Q-MEM</b><span>${Math.round(meter.mem*100)}%</span><i style="width:${meter.mem*100}%"></i></div></div>
    <p class="muted">${st.backend || ""} · CPython ${st.python || st.version || ""} · numpy ${st.numpy || ""} · ${st.n_qubits || 28}q float64 · entropy ${meter.entropy.toFixed(3)} · syscalls ${meter.sys}</p>
    <div class="qubits">${bloch.map((b,i)=>`<div class="q"><canvas width="56" height="56" data-q="${i}"></canvas><span>q${b.q ?? i}</span></div>`).join("")}</div>
    <table><thead><tr><th>窗口</th><th>状态</th><th>CPU</th><th>MEM</th></tr></thead><tbody>${windows.map(w=>`<tr><td>${w.title}</td><td>${w.min?"sleep":w.id===focus?"focus":"run"}</td><td>${w.min?"1%":w.id===focus?Math.round(meter.cpu*100)+"%":Math.round(meter.cpu*35)+"%"}</td><td>${w.min?"3%":"12%"}</td></tr>`).join("")}</tbody></table>`;
  queueMicrotask(() => box.querySelectorAll("canvas").forEach(c => drawBloch(c, bloch[Number(c.dataset.q)])));
  return box;
}

function aboutView() {
  const n = lastStatus;
  const box = el("div", "pad");
  const rows = [
    ["后端", n.backend],
    ["解释器", "CPython " + (n.python || n.version)],
    ["可执行文件", n.executable],
    ["引擎", n.engine],
    ["量子比特", (n.n_qubits ?? 28) + " × float64"],
    ["目标寄存器", (n.target_qubits ?? 28) + "q"],
    ["态矢量", fmtBytes(n.sv_bytes)],
    ["numpy", n.numpy],
    ["噪声", "无"],
    ["门保真度", "100%"],
    ["系统调用", n.syscalls],
  ];
  box.innerHTML = `<h2>Ket OS</h2><p class="muted">量子计算在内置 CPython 3.12 + numpy 里跑，浏览器只负责画桌面。默认 28 个双精度量子比特。</p>
    <dl>${rows.map(([k,v])=>`<div><dt>${k}</dt><dd class="mono">${v ?? ""}</dd></div>`).join("")}</dl>`;
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
  box.append(el("p","muted",`系统寄存器 · ${nq} × float64 · numpy 向量化内核`), row, qs);
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
  const n = el("div", "win" + (w.id===focus?" focus":"") + (w.min?" min":""));
  n.style.left = (w.max?0:w.x)+"px";
  n.style.top = (w.max?0:w.y)+"px";
  n.style.width = (w.max?innerWidth:w.w)+"px";
  n.style.height = (w.max?innerHeight-48:w.h)+"px";
  n.style.zIndex = String(w.z);
  if (w.min) n.style.display = "none";
  const title = el("div", "title");
  title.append(el("span", "", w.title));
  const btns = el("div", "wbtn");
  const mn = el("button", "", "–"); mn.onclick = e => { e.stopPropagation(); w.min = true; paint(); };
  const mx = el("button", "", "□"); mx.onclick = e => { e.stopPropagation(); w.max = !w.max; paint(); };
  const cl = el("button", "", "×"); cl.onclick = e => { e.stopPropagation(); closeWin(w.id); };
  btns.append(mn, mx, cl); title.append(btns);
  let drag = null;
  title.onpointerdown = e => {
    if (w.max) return;
    focus = w.id; w.z = ++zTop;
    drag = {dx:e.clientX-w.x, dy:e.clientY-w.y};
    e.target.setPointerCapture(e.pointerId);
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
  const desk = el("div", "desk");
  const nav = el("nav", "icons");
  APPS.forEach(a => {
    const b = el("button", "icon");
    b.innerHTML = `<span>${a.title[0]}</span><em>${a.title}</em>`;
    b.onclick = () => openApp(a.id);
    nav.append(b);
  });
  desk.append(nav);
  windows.forEach(w => desk.append(winEl(w)));
  if (startOpen) {
    const s = el("div", "start");
    APPS.forEach(a => { const b = el("button","",a.title); b.onclick = () => openApp(a.id); s.append(b); });
    desk.append(s);
  }
  const dock = el("footer", "dock");
  const ketBtn = el("button", "ket", "Ket");
  ketBtn.onclick = () => { startOpen = !startOpen; paint(); };
  dock.append(ketBtn);
  windows.forEach(w => {
    const b = el("button", w.id===focus && !w.min ? "on" : "", w.title);
    b.onclick = () => { w.min = false; focus = w.id; w.z = ++zTop; paint(); };
    dock.append(b);
  });
  const tray = el("div", "tray");
  tray.innerHTML = `<span id="cpu">cpu ${Math.round(meter.cpu*100)}%</span>
    <span id="mem">mem ${Math.round(meter.mem*100)}%</span>
    <span>CPython ${lastStatus.python || ""}</span>
    <span id="nq">${lastStatus.n_qubits || 28}q f64</span>
    <span id="clock">${new Date().toLocaleTimeString()}</span>`;
  dock.append(tray);
  desk.append(dock);
  root.append(desk);
}

async function boot() {
  const root = document.getElementById("root");
  try {
    const st = await ket("boot");
    const btn = el("button", "boot");
    btn.innerHTML = `<div class="mark">⟩</div><h1>Ket OS</h1>
      <p>内置 CPython ${st.python || st.version} + numpy ${st.numpy || ""} · ${st.n_qubits} × float64 · 无噪声 · F = 1</p>
      <pre>${(st.log||[]).join("\n")}</pre>
      <p>点击进入桌面</p>`;
    btn.onclick = () => {
      root.innerHTML = "";
      paint();
      const ms = (st.n_qubits || 0) >= 24 ? 2000 : 1000;
      setInterval(tick, ms);
    };
    root.append(btn);
  } catch (err) {
    root.innerHTML = `<div class="err">无法连接 CPython 内核：${err}<br>请用 START 脚本启动，不要直接打开 HTML。</div>`;
  }
}
boot();
