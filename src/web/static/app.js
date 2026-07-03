/* audiolayers gui — stato controlli -> API -> wav */
"use strict";

/* Definizione parametri: rispecchia bounds e default del motore.
   env: true = envelope-abile (editor breakpoint). */
const GLOBAL_DEFS = [
  { path: "sample_rate", label: "sample rate", kind: "select",
    options: [44100, 48000, 96000], def: 48000 },
  { path: "seed", label: "seed", kind: "int", def: 424242 },
  { path: "master_volume", label: "master (dB)", min: -60, max: 12, step: 0.5, def: 0, env: true },
];
const LAYER_DEFS = [
  { path: "duration", label: "durata (s)", min: 1, max: 300, step: 1, def: 20 },
  { path: "onset", label: "onset (s)", min: 0, max: 300, step: 0.5, def: 0 },
  { path: "fill_factor", label: "fill factor", min: 0.05, max: 5, step: 0.05, def: 1, env: true },
  { path: "distribution", label: "distribution", min: 0, max: 1, step: 0.01, def: 0, env: true },
  { path: "fragment.duration", label: "grano (s)", min: 0.001, max: 2, step: 0.001, def: 0.5, env: true },
  { path: "fragment.duration_range", label: "grano ± (s)", min: 0, max: 1, step: 0.001, def: 0, env: true },
  { path: "fragment.envelope", label: "inviluppo", kind: "select",
    options: ["raised_cosine", "rectangle"], def: "raised_cosine" },
  { path: "fragment.attack", label: "attack (s)", min: 0, max: 0.1, step: 0.001, def: 0.008 },
  { path: "fragment.release", label: "release (s)", min: 0, max: 0.1, step: 0.001, def: 0.01 },
  { path: "pointer.start", label: "pointer", min: 0, max: 1, step: 0.01, def: 0, env: true },
  { path: "pointer.start_range", label: "pointer ±", min: 0, max: 1, step: 0.01, def: 0, env: true },
  { path: "pointer.overflow", label: "overflow", kind: "select",
    options: ["clamp_back", "loop", "zero_pad"], def: "clamp_back" },
  { path: "selection.strategy", label: "selezione", kind: "select",
    options: ["sequential", "rotation", "random"], def: "sequential" },
  { path: "volume", label: "volume (dB)", min: -60, max: 12, step: 0.5, def: 0, env: true },
  { path: "volume_range", label: "volume ± (dB)", min: 0, max: 12, step: 0.5, def: 0, env: true },
  { path: "pan", label: "pan (°)", min: -360, max: 360, step: 1, def: 0, env: true },
  { path: "pan_range", label: "pan ± (°)", min: 0, max: 180, step: 1, def: 0, env: true },
];

const state = { global: {}, layers: [] };
let layerCounter = 0;

function newControl(def, enabled = false) {
  return { enabled, value: def.def };
}

function newLayer() {
  layerCounter += 1;
  const params = {};
  for (const def of LAYER_DEFS) params[def.path] = newControl(def, def.path === "duration");
  return { layer_id: `layer${String(layerCounter).padStart(2, "0")}`,
           pool: "audio/pool/", params };
}

/* ---------- envelope editor ---------- */
function drawEnvelope(canvas, def, control, layerDur) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width = canvas.clientWidth * 2;
  const H = canvas.height = 112;
  ctx.clearRect(0, 0, W, H);
  ctx.strokeStyle = "#eee";
  for (let i = 1; i < 4; i++) {
    ctx.beginPath(); ctx.moveTo(0, H * i / 4); ctx.lineTo(W, H * i / 4); ctx.stroke();
  }
  const pts = control.value;
  ctx.strokeStyle = "#111"; ctx.fillStyle = "#111"; ctx.lineWidth = 2;
  ctx.beginPath();
  pts.forEach(([t, v], i) => {
    const x = (t / layerDur) * W;
    const y = H - ((v - def.min) / (def.max - def.min)) * H;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
  pts.forEach(([t, v]) => {
    const x = (t / layerDur) * W;
    const y = H - ((v - def.min) / (def.max - def.min)) * H;
    ctx.beginPath(); ctx.arc(x, y, 5, 0, 7); ctx.fill();
  });
}

function attachEnvelopeEditor(canvas, def, control, getDur) {
  const toPoint = (ev) => {
    const r = canvas.getBoundingClientRect();
    const t = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)) * getDur();
    const v = def.min + Math.max(0, Math.min(1, 1 - (ev.clientY - r.top) / r.height)) * (def.max - def.min);
    return [Number(t.toFixed(3)), Number(v.toFixed(4))];
  };
  const nearest = (ev) => {
    const r = canvas.getBoundingClientRect();
    let best = -1, bestD = 14;
    control.value.forEach(([t, v], i) => {
      const x = (t / getDur()) * r.width;
      const y = r.height - ((v - def.min) / (def.max - def.min)) * r.height;
      const d = Math.hypot(x - (ev.clientX - r.left), y - (ev.clientY - r.top));
      if (d < bestD) { bestD = d; best = i; }
    });
    return best;
  };
  let dragging = -1;
  const redraw = () => drawEnvelope(canvas, def, control, getDur());
  canvas.addEventListener("pointerdown", (ev) => {
    const hit = nearest(ev);
    if (ev.button === 2 || ev.detail === 2) {           // destro/doppio: rimuovi
      if (hit >= 0 && control.value.length > 2) { control.value.splice(hit, 1); redraw(); }
      return;
    }
    if (hit >= 0) { dragging = hit; }
    else { control.value.push(toPoint(ev));
           control.value.sort((a, b) => a[0] - b[0]);
           dragging = control.value.findIndex(p => p[0] === toPoint(ev)[0]); }
    canvas.setPointerCapture(ev.pointerId);
    redraw();
  });
  canvas.addEventListener("pointermove", (ev) => {
    if (dragging < 0) return;
    control.value[dragging] = toPoint(ev);
    control.value.sort((a, b) => a[0] - b[0]);
    redraw();
  });
  canvas.addEventListener("pointerup", () => { dragging = -1; });
  canvas.addEventListener("contextmenu", (ev) => ev.preventDefault());
  redraw();
}

/* ---------- righe parametro ---------- */
function paramRow(def, control, getDur) {
  const row = document.createElement("div");
  row.className = "param" + (control.enabled ? "" : " off");

  const chk = document.createElement("input");
  chk.type = "checkbox"; chk.checked = control.enabled;
  chk.onchange = () => { control.enabled = chk.checked; row.classList.toggle("off", !chk.checked); };

  const name = document.createElement("span");
  name.className = "name"; name.textContent = def.label;

  const slot = document.createElement("span");
  const val = document.createElement("span"); val.className = "value";

  const showScalar = () => {
    slot.innerHTML = ""; val.textContent = "";
    if (def.kind === "select") {
      const sel = document.createElement("select");
      for (const o of def.options) {
        const opt = document.createElement("option");
        opt.value = o; opt.textContent = o;
        if (String(o) === String(control.value)) opt.selected = true;
        sel.append(opt);
      }
      sel.onchange = () => { control.value = def.options[sel.selectedIndex]; };
      slot.append(sel);
    } else if (def.kind === "int") {
      const num = document.createElement("input");
      num.type = "number"; num.value = control.value;
      num.onchange = () => { control.value = parseInt(num.value, 10) || 0; };
      slot.append(num);
    } else {
      const rng = document.createElement("input");
      rng.type = "range"; rng.min = def.min; rng.max = def.max; rng.step = def.step;
      rng.value = Array.isArray(control.value) ? def.def : control.value;
      val.textContent = rng.value;
      rng.oninput = () => { control.value = parseFloat(rng.value); val.textContent = rng.value; };
      slot.append(rng);
    }
  };

  row.append(chk, name, slot, val);

  if (def.env) {
    const envBtn = document.createElement("button");
    envBtn.className = "envbtn"; envBtn.textContent = "env"; envBtn.title = "curva nel tempo";
    let envRow = null;
    const openEditor = () => {
      envBtn.classList.add("on");
      if (!Array.isArray(control.value))
        control.value = [[0, control.value], [getDur(), control.value]];
      slot.innerHTML = ""; val.textContent = "curva";
      envRow = document.createElement("div");
      envRow.className = "envrow";
      const cv = document.createElement("canvas");
      cv.className = "envelope";
      envRow.append(cv);
      row.after(envRow);
      attachEnvelopeEditor(cv, def, control, getDur);
    };
    envBtn.onclick = () => {
      if (envBtn.classList.contains("on")) {
        envBtn.classList.remove("on");
        control.value = control.value[0][1];
        if (envRow) envRow.remove();
        showScalar();
      } else openEditor();
    };
    name.append(" ", envBtn);
    if (Array.isArray(control.value)) { showScalar(); queueMicrotask(openEditor); }
    else showScalar();
  } else showScalar();

  return row;
}

/* ---------- pannelli ---------- */
function renderGlobals() {
  const box = document.getElementById("global-params");
  box.innerHTML = "";
  for (const def of GLOBAL_DEFS) {
    if (!state.global[def.path]) state.global[def.path] = newControl(def);
    box.append(paramRow(def, state.global[def.path], () => 60));
  }
}

function renderLayers() {
  const main = document.getElementById("layers");
  main.innerHTML = "";
  state.layers.forEach((layer, idx) => {
    const panel = document.createElement("section");
    panel.className = "panel";
    const head = document.createElement("div");
    head.className = "layer-head";
    const id = document.createElement("input");
    id.type = "text"; id.value = layer.layer_id;
    id.onchange = () => { layer.layer_id = id.value; };
    const pool = document.createElement("input");
    pool.type = "text"; pool.value = layer.pool; pool.title = "pool";
    pool.onchange = () => { layer.pool = pool.value; };
    const del = document.createElement("button");
    del.className = "danger"; del.textContent = "×";
    del.onclick = () => { state.layers.splice(idx, 1); renderLayers(); };
    head.append(id, pool, del);
    panel.append(head);
    const grid = document.createElement("div");
    grid.className = "params";
    const getDur = () => {
      const d = layer.params["duration"];
      return (d.enabled && !Array.isArray(d.value)) ? d.value : 20;
    };
    for (const def of LAYER_DEFS) {
      if (!layer.params[def.path]) layer.params[def.path] = newControl(def);
      grid.append(paramRow(def, layer.params[def.path], getDur));
    }
    panel.append(grid);
    main.append(panel);
  });
}

/* ---------- azioni ---------- */
const status = (msg, err) => {
  const el = document.getElementById("status");
  el.textContent = msg; el.classList.toggle("error", !!err);
};

async function doRender() {
  status("render in corso…");
  document.getElementById("player").hidden = true;
  document.getElementById("btn-download").hidden = true;
  const dig = document.getElementById("chk-dig").checked;
  const res = await fetch("/api/render", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state, dig }),
  });
  const { job_id } = await res.json();
  const poll = setInterval(async () => {
    const s = await (await fetch(`/api/jobs/${job_id}`)).json();
    if (s.state === "running") { status(dig ? "download + render…" : "render…"); return; }
    clearInterval(poll);
    if (s.state === "error") { status(`errore: ${s.detail}`, true); return; }
    status("fatto");
    const url = `/api/jobs/${job_id}/audio`;
    const player = document.getElementById("player");
    player.src = url; player.hidden = false; player.play().catch(() => {});
    const dl = document.getElementById("btn-download");
    dl.href = url; dl.hidden = false;
  }, 500);
}

async function doExport() {
  const res = await fetch("/api/yaml", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state }),
  });
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "score.yaml"; a.click();
}

async function doImport(file) {
  const text = await file.text();
  const res = await fetch("/api/import", {
    method: "POST", headers: { "Content-Type": "text/yaml" }, body: text,
  });
  const imported = await res.json();
  state.global = {};
  for (const def of GLOBAL_DEFS)
    state.global[def.path] = imported.global[def.path] ?? newControl(def);
  state.layers = imported.layers.map((l) => {
    const layer = newLayer();
    layer.layer_id = l.layer_id; layer.pool = l.pool;
    for (const def of LAYER_DEFS)
      layer.params[def.path] = l.params[def.path] ?? newControl(def);
    return layer;
  });
  renderGlobals(); renderLayers();
  status("yaml importato");
}

document.getElementById("btn-add-layer").onclick = () => {
  state.layers.push(newLayer()); renderLayers();
};
document.getElementById("btn-render").onclick = doRender;
document.getElementById("btn-export").onclick = doExport;
document.getElementById("file-import").onchange = (ev) => {
  if (ev.target.files[0]) doImport(ev.target.files[0]);
};

state.layers.push(newLayer());
renderGlobals();
renderLayers();
