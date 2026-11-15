// Dashboard: variable switcher (temperature / precipitation / dry days), time-period selector, regression stats,
// gist, trend chart, and a Leaflet trend map that colours every state by its trend.
// Monthly CSVs: data/processed/regional_timeseries/{t2m,prectot,cdd}_{state,india}_monthly.csv
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const $ = s => document.querySelector(s);

/* ---------- reusable time period selector ---------- */
function createTimePeriodSelector(root, { startYear = 2000, endYear = 2025, defaultEnd = endYear, onChange = () => {} } = {}) {
  const yrs = id => `<select id="${id}">` + Array.from({ length: endYear - startYear + 1 }, (_, i) => endYear - i).map(y => `<option>${y}</option>`).join("") + "</select>";
  root.innerHTML = `
    <div class="seg">
      <button data-m="range" class="on">Year range</button><button data-m="ym">Year &amp; months</button><button data-m="one">One month, all years</button></div>
    <div class="ctl on" data-c="range">${yrs("ya")}<span class="to">to</span>${yrs("yb")}</div>
    <div class="ctl" data-c="ym">${yrs("yc")}<div class="chips">${MONTHS.map((m, i) => `<label><input type="checkbox" value="${i}"><span>${m}</span></label>`).join("")}</div></div>
    <div class="ctl" data-c="one"><select id="mo">${MONTHS.map((m, i) => `<option value="${i}">${m}</option>`).join("")}</select><span class="to">in every year</span></div>`;
  const q = s => root.querySelector(s);
  q("#ya").value = startYear; q("#yb").value = defaultEnd; q("#yc").value = endYear;
  let mode = "range";
  const get = () => ({
    mode, a: +q("#ya").value, b: +q("#yb").value, year: +q("#yc").value,
    months: [...root.querySelectorAll(".chips input:checked")].map(c => +c.value), month: +q("#mo").value
  });
  root.querySelectorAll(".seg button").forEach(b => b.onclick = () => {
    mode = b.dataset.m;
    root.querySelectorAll(".seg button").forEach(x => x.classList.toggle("on", x === b));
    root.querySelectorAll(".ctl").forEach(c => c.classList.toggle("on", c.dataset.c === mode));
    onChange(get());
  });
  root.onchange = () => onChange(get());
  return { get };
}

/* ---------- variables ---------- */
const VARS = {
  t2m:  { name: "Temperature", title: "temperature", file: "t2m", unit: "°C", tick: "°", d: 2, sd: 3, agg: "mean", color: "#3454d1",
          neg: [52, 84, 209], pos: [196, 69, 45], noun: "mean temperature",
          note: "Data: monthly mean 2 m air temperature (°C) per state/UT from t2m_*_monthly.csv. Annual values are the mean of the months." },
  prec: { name: "Precipitation", title: "precipitation", file: "prectot", unit: "mm", tick: "", d: 1, sd: 2, agg: "sum", color: "#1b9e8a",
          neg: [181, 101, 29], pos: [27, 158, 138], noun: "total precipitation",
          note: "Data: monthly total precipitation (mm, MERRA-2 PRECTOT) per state/UT from prectot_*_monthly.csv. Annual values are totals (12 × the mean month)." },
  cdd:  { name: "Dry days (CDD)", title: "consecutive dry days", file: "cdd", unit: "days", tick: "", d: 2, sd: 3, agg: "mean", color: "#c4452d",
          neg: [27, 158, 138], pos: [196, 69, 45], noun: "consecutive dry days per month",
          note: "Data: monthly consecutive dry days (days) per state/UT from cdd_*_monthly.csv. Annual values are the mean of the months." }
};
let VAR = "t2m";
const DATA = {};   // DATA[key] = { series, minYear, maxYear, lastFull }, loaded on first use

/* ---------- monthly CSVs ---------- */
// Tried in order, so this works whether the page is served from the project root or from UI/
const DATA_DIRS = ["data/processed/regional_timeseries/", "../data/processed/regional_timeseries/"];
async function getText(name) {
  let err;
  for (const d of DATA_DIRS) {
    try { const r = await fetch(d + name); if (r.ok) return await r.text(); err = new Error(d + name + " (" + r.status + ")"); }
    catch (e) { err = e; }
  }
  throw err;
}
function parseCSV(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) continue;
    const cells = []; let cur = "", quoted = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (quoted) { if (ch === '"') { if (line[i + 1] === '"') { cur += '"'; i++; } else quoted = false; } else cur += ch; }
      else if (ch === '"') quoted = true;
      else if (ch === ",") { cells.push(cur); cur = ""; }
      else cur += ch;
    }
    cells.push(cur); rows.push(cells);
  }
  const head = rows.shift().map(s => s.trim());
  return rows.map(r => Object.fromEntries(head.map((k, i) => [k, r[i]])));
}
const norm = s => String(s).toLowerCase().replace(/&/g, "and").replace(/[^a-z0-9]/g, "");
// State names differ between map.js and the CSVs (e.g. "Andaman and Nicobar" vs "... Islands"), so match on a canonical key
const ALIAS = { pondicherry: "puducherry", orissa: "odisha", uttaranchal: "uttarakhand", dadraandnagarhaveli: "dnhdd", damananddiu: "dnhdd", dadraandnagarhavelianddamananddiu: "dnhdd" };
const skey = s => { const k = norm(s).replace(/^nctof/, "").replace(/islands$/, ""); return ALIAS[k] || k; };
// series[normalisedName] = { year: [12 monthly values, null where missing] }
function addRows(series, rows, nameOf) {
  if (!rows.length) return;
  const col = Object.keys(rows[0]).find(k => /^mean_/i.test(k));
  if (!col) throw new Error("no mean_* column in CSV");
  for (const row of rows) {
    const v = parseFloat(row[col]), d = String(row.date || "");
    if (!isFinite(v) || d.length < 7) continue;
    const y = +d.slice(0, 4), m = +d.slice(5, 7) - 1, key = skey(nameOf(row));
    ((series[key] ??= {})[y] ??= Array(12).fill(null))[m] = v;
  }
}
const MIN_MONTHS = 6; // a year needs at least this many months of data to be used
async function loadVar(key) {
  if (DATA[key]) return DATA[key];
  const V = VARS[key], series = {};
  addRows(series, parseCSV(await getText(V.file + "_state_monthly.csv")), r => r.state_ut);
  const states = Object.keys(series);
  try { addRows(series, parseCSV(await getText(V.file + "_india_monthly.csv")), () => "India"); } catch (e) { console.warn("India CSV not loaded:", e.message); }
  if (!series.india) { // fallback: unweighted mean of the states
    const ind = {};
    states.forEach(k => Object.entries(series[k]).forEach(([y, arr]) => arr.forEach((v, m) => {
      if (v == null) return; const a = (ind[y] ??= Array.from({ length: 12 }, () => []))[m]; a.push(v); })));
    series.india = Object.fromEntries(Object.entries(ind).map(([y, a]) => [y, a.map(x => x.length ? x.reduce((s, v) => s + v) / x.length : null)]));
  }
  if (key === "t2m") { // safety: Kelvin -> degC (same guard as the training script)
    let sum = 0, n = 0; Object.values(series).forEach(o => Object.values(o).forEach(a => a.forEach(v => { if (v != null) { sum += v; n++; } })));
    if (n && sum / n > 150) Object.values(series).forEach(o => Object.values(o).forEach(a => a.forEach((v, i) => { if (v != null) a[i] = v - 273.15; })));
  }
  const years = Object.values(series).flatMap(o => Object.keys(o).map(Number));
  const full = Object.keys(series.india).map(Number).filter(y => series.india[y].filter(v => v != null).length >= MIN_MONTHS);
  return DATA[key] = { series, minYear: Math.min(...years), maxYear: Math.max(...years), lastFull: full.length ? Math.max(...full) : Math.max(...years) };
}

const _clim = {};
function climatology(r, S) { // long-term mean of each calendar month (cached per variable and region)
  const k = VAR + skey(r); if (_clim[k]) return _clim[k];
  return _clim[k] = MONTHS.map((_, m) => { const v = Object.values(S).map(a => a[m]).filter(x => x != null); return v.length ? v.reduce((t, x) => t + x, 0) / v.length : NaN; });
}
function getSeries(r, p) {
  const D = DATA[VAR], V = VARS[VAR], S = D && D.series[skey(r)];
  if (!S) return null;
  if (p.mode === "range") {
    // Annual value. A year with a few missing months is kept: each month is compared with its own long-term
    // average, so a missing month does not bias a partial year. Precipitation is a total (12 x the mean month).
    const a = Math.min(p.a, p.b), b = Math.max(p.a, p.b), pts = [], c = climatology(r, S), k = V.agg === "sum" ? 12 : 1;
    const base = c.reduce((t, v) => t + v, 0) / 12;
    for (let y = a; y <= b; y++) {
      const m = S[y]; if (!m) continue;
      const have = m.map((v, i) => v == null ? null : v - c[i]).filter(v => v != null);
      if (have.length < MIN_MONTHS) continue;
      const n = have.length, val = k * (base + have.reduce((t, v) => t + v, 0) / n);
      pts.push({ x: y, label: n < 12 ? `${y} (${n} of 12 months)` : y, y: val });
    }
    return { pts, scale: 10, unit: "per decade", span: pts.length ? `${pts[0].x}–${pts[pts.length - 1].x}` : `${a}–${b}`, xl: "Year" };
  }
  if (p.mode === "ym") {
    const ms = (p.months.length ? p.months : MONTHS.map((_, i) => i)).slice().sort((a, b) => a - b);
    const pts = ms.filter(m => S[p.year] && S[p.year][m] != null).map(m => ({ x: m, label: MONTHS[m] + " " + p.year, y: S[p.year][m] }));
    return { pts, scale: 1, unit: "per month", span: `${p.year}${p.months.length ? " (" + ms.map(m => MONTHS[m]).join(", ") + ")" : ""}`, xl: "Month" };
  }
  // one calendar month across every year
  const pts = [];
  for (let y = D.minYear; y <= D.maxYear; y++) if (S[y] && S[y][p.month] != null) pts.push({ x: y, label: MONTHS[p.month] + " " + y, y: S[y][p.month] });
  return { pts, scale: 10, unit: "per decade", span: pts.length ? `${MONTHS[p.month]}, ${pts[0].x}–${pts[pts.length - 1].x}` : MONTHS[p.month], xl: "Year" };
}

/* ---------- regression ---------- */
function betacf(a, b, x) { let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap, h; d = 1 / (Math.abs(d) < 1e-30 ? 1e-30 : d); h = d;
  for (let m = 1; m <= 200; m++) { const m2 = 2 * m; let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
    d = 1 + aa * d; d = 1 / (Math.abs(d) < 1e-30 ? 1e-30 : d); c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30; h *= d * c;
    aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2)); d = 1 + aa * d; d = 1 / (Math.abs(d) < 1e-30 ? 1e-30 : d);
    c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30; const del = d * c; h *= del; if (Math.abs(del - 1) < 3e-10) break; } return h; }
function lgam(x) { const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, .1208650973866179e-2, -.5395239384953e-5]; let y = x, t = x + 5.5; t -= (x + .5) * Math.log(t); let s = 1.000000000190015; for (const k of c) s += k / ++y; return -t + Math.log(2.5066282746310005 * s / x); }
function betai(a, b, x) { if (x <= 0) return 0; if (x >= 1) return 1; const bt = Math.exp(lgam(a + b) - lgam(a) - lgam(b) + a * Math.log(x) + b * Math.log(1 - x));
  return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b; }
function tcrit(df) { // two-sided 95% critical t value
  if (df < 1) return NaN; let lo = 0, hi = 1000;
  for (let i = 0; i < 60; i++) { const mid = (lo + hi) / 2; if (betai(df / 2, .5, df / (df + mid * mid)) > 0.05) lo = mid; else hi = mid; }
  return (lo + hi) / 2;
}
function regress(pts) {
  const n = pts.length, x0 = pts[0].x, xs = pts.map(p => p.x - x0), ys = pts.map(p => p.y);
  const mx = xs.reduce((a, b) => a + b) / n, my = ys.reduce((a, b) => a + b) / n;
  let sxx = 0, sxy = 0; xs.forEach((x, i) => { sxx += (x - mx) ** 2; sxy += (x - mx) * (ys[i] - my); });
  const b = n > 1 && sxx ? sxy / sxx : 0, a = my - b * mx;
  let sse = 0; xs.forEach((x, i) => sse += (ys[i] - a - b * x) ** 2);
  const df = n - 2, se = df > 0 && sxx ? Math.sqrt(sse / df / sxx) : 0, t = se ? b / se : 0;
  let syy = 0; ys.forEach(y => syy += (y - my) ** 2);
  return { b, a, x0, se, df, r2: syy ? 1 - sse / syy : 0, ci: df > 0 ? tcrit(df) * se : NaN,
    p: df > 0 && se ? betai(df / 2, .5, df / (df + t * t)) : 1, change: b * (xs[n - 1] - xs[0]) };
}

/* ---------- rendering ---------- */
const region = () => (typeof selected !== "undefined" && selected) ? selected : "India";
const fmt = (v, d = 2) => (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(d);
let selector, last, trendLegend;

function refresh() {
  if (!DATA[VAR] || !selector) return;
  const V = VARS[VAR], r = region(), p = selector.get(), s = getSeries(r, p), u = " " + V.unit;
  $("#region").textContent = r;
  paintMap(p);
  if (!s || s.pts.length < 3) {
    last = null; $("#chart").innerHTML = "";
    $("#change").className = "big"; $("#change").textContent = "–";
    ["pv","sl","ic","r2","se","ci","np","mean","sd","hi","lo","fit"].forEach(i => $("#" + i).textContent = "–");
    $("#csub").textContent = r;
    $("#gist").textContent = !s
      ? `No ${V.title} data found for ${r}.`
      : `Not enough ${V.title} data for this selection (at least three points are needed). Years with fewer than ${MIN_MONTHS} months of data are skipped in the annual view.`;
    return;
  }
  const st = regress(s.pts), sig = st.p < 0.05;
  $("#change").className = "big " + (st.change > 0 ? "up" : "");
  $("#change").innerHTML = `${fmt(st.change, V.d)}<small>${V.unit} over ${s.span}</small>`;
  $("#pv").textContent = st.p < 0.001 ? "< 0.001" : st.p.toFixed(3);
  $("#sl").textContent = fmt(st.b * s.scale, V.sd) + u;
  $("#slu").textContent = "Slope " + s.unit;
  $("#ic").textContent = st.a.toFixed(1) + u;
  const ys = s.pts.map(q => q.y), n = ys.length, mean = ys.reduce((t, v) => t + v, 0) / n,
    sd = Math.sqrt(ys.reduce((t, v) => t + (v - mean) ** 2, 0) / (n - 1)),
    hiP = s.pts.reduce((a, b) => b.y > a.y ? b : a), loP = s.pts.reduce((a, b) => b.y < a.y ? b : a),
    fitAt = x => st.a + st.b * (x - st.x0), xa = s.pts[0].x, xb = s.pts[n - 1].x;
  $("#r2").textContent = st.r2.toFixed(3);
  $("#se").textContent = "± " + (st.se * s.scale).toFixed(V.sd) + u;
  $("#seu").textContent = "Std. error " + s.unit;
  $("#ci").textContent = isFinite(st.ci) ? `${fmt((st.b - st.ci) * s.scale, 2)} to ${fmt((st.b + st.ci) * s.scale, 2)}${u}` : "–";
  $("#np").textContent = n;
  $("#mean").textContent = mean.toFixed(V.d) + u;
  $("#sd").textContent = sd.toFixed(V.d) + u;
  $("#hi").textContent = hiP.y.toFixed(V.d) + u;
  $("#hil").textContent = "Highest · " + hiP.label;
  $("#lo").textContent = loP.y.toFixed(V.d) + u;
  $("#lol").textContent = "Lowest · " + loP.label;
  $("#fit").textContent = `${fitAt(xa).toFixed(1)} → ${fitAt(xb).toFixed(1)}${u}`;
  $("#gist").textContent = `In ${r}, ${V.noun} ${st.change >= 0 ? "rose" : "fell"} by about ${Math.abs(st.change).toFixed(V.d)} ${V.unit} across ${s.span}, a rate of ${fmt(st.b * s.scale, V.sd)} ${V.unit} ${s.unit}. ` +
    (sig ? "The trend is statistically significant (p < 0.05), so it is unlikely to be random variation." : "The trend is not statistically significant (p ≥ 0.05), so this change could be natural variability.");
  $("#ctitle").textContent = V.name + " trend";
  $("#csub").textContent = `${r} · ${s.span} · ${V.unit}${p.mode === "range" ? ", " + (V.agg === "sum" ? "annual total" : "annual mean") : ""}`;
  last = { s, st }; draw();
}

function draw() {
  if (!last) return;
  const V = VARS[VAR], { s, st } = last, el = $("#chart"), W = el.clientWidth || 800, H = 300, m = { l: 46, r: 14, t: 12, b: 30 };
  const xs = s.pts.map(p => p.x), ys = s.pts.map(p => p.y);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), yl = Math.min(...ys), yh = Math.max(...ys), pad = (yh - yl) * .12 || 1;
  const y0 = yl - pad, y1 = yh + pad, X = x => m.l + (x - x0) / (x1 - x0 || 1) * (W - m.l - m.r), Y = y => H - m.b - (y - y0) / (y1 - y0) * (H - m.t - m.b);
  const line = s.pts.map((p, i) => (i ? "L" : "M") + X(p.x).toFixed(1) + " " + Y(p.y).toFixed(1)).join("");
  const fit = v => st.a + st.b * (v - st.x0), dg = y1 - y0 >= 20 ? 0 : 1;
  let g = "";
  for (let i = 0; i <= 4; i++) { const v = y0 + (y1 - y0) * i / 4; g += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e4e8e7"/><text x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end" font-size="11.5" fill="#6c7776">${v.toFixed(dg)}${V.tick}</text>`; }
  const tk = Math.min(7, s.pts.length);
  for (let i = 0; i < tk; i++) { const p = s.pts[Math.round(i * (s.pts.length - 1) / (tk - 1 || 1))]; g += `<text x="${X(p.x)}" y="${H - 8}" text-anchor="middle" font-size="11.5" fill="#6c7776">${s.xl === "Month" ? MONTHS[p.x] : p.x}</text>`; }
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" height="${H}" role="img" aria-label="${V.name} trend chart">${g}
    <path d="${line}" fill="none" stroke="${V.color}" stroke-width="2.2" stroke-linejoin="round"/>
    <line x1="${X(x0)}" y1="${Y(fit(x0))}" x2="${X(x1)}" y2="${Y(fit(x1))}" stroke="#16201f" stroke-width="1.6" stroke-dasharray="5 5"/>
    <circle id="dot" r="5" fill="${V.color}" stroke="#fff" stroke-width="2" style="display:none"/></svg><div class="tip"></div>`;
  const svg = el.querySelector("svg"), dot = el.querySelector("#dot"), tip = el.querySelector(".tip");
  svg.onmousemove = e => {
    const bx = svg.getBoundingClientRect(), mx = (e.clientX - bx.left) * W / bx.width;
    const p = s.pts.reduce((a, b) => Math.abs(X(b.x) - mx) < Math.abs(X(a.x) - mx) ? b : a);
    dot.style.display = ""; dot.setAttribute("cx", X(p.x)); dot.setAttribute("cy", Y(p.y));
    tip.textContent = `${p.label}: ${p.y.toFixed(V.d)} ${V.unit}`; tip.style.left = X(p.x) * bx.width / W + "px"; tip.style.top = Y(p.y) * bx.height / H + "px"; tip.style.opacity = 1;
  };
  svg.onmouseleave = () => { dot.style.display = "none"; tip.style.opacity = 0; };
}

/* ---------- trend map: colour each state on the Leaflet map by its trend ---------- */
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const trendColor = (V, t) => `rgb(${mix([244, 241, 234], t < 0 ? V.neg : V.pos, Math.abs(t)).map(Math.round)})`;
function paintMap(p) {
  const V = VARS[VAR], val = {}, per = p.mode === "ym" ? "per month" : "per decade";
  STATES.forEach(f => { const s = getSeries(f.properties.n, p); if (s && s.pts.length >= 3) val[f.properties.n] = regress(s.pts).b * s.scale; });
  const mx = Math.max(1e-9, ...Object.values(val).map(Math.abs));
  STATES.forEach(f => {
    const n = f.properties.n, v = val[n];
    f.properties.color = v == null ? "#cfd6dd" : trendColor(V, v / mx);
    stateLayers[n].setTooltipContent(v == null ? n + ": no data" : `${n}: ${fmt(v, V.sd)} ${V.unit} ${per}`);
  });
  statesLayer.setStyle(stateStyle);
  if (!trendLegend) { trendLegend = L.control({ position: "bottomleft" }); trendLegend.onAdd = () => (trendLegend._div = L.DomUtil.create("div", "panel")); trendLegend.addTo(map); }
  trendLegend._div.style.display = selected ? "none" : "";
  trendLegend._div.innerHTML = `<b>${V.name} trend</b><div style="height:8px;width:180px;margin:6px 0 3px;border-radius:2px;background:linear-gradient(90deg,${trendColor(V, -1)},${trendColor(V, 0)},${trendColor(V, 1)})"></div>` +
    `<div style="display:flex;justify-content:space-between;gap:8px"><span>${fmt(-mx, V.sd)}</span><span>${V.unit} ${per}</span><span>${fmt(mx, V.sd)}</span></div>`;
}

/* ---------- wire up ---------- */
// map.js fires "regionchange" whenever the selection changes (state click, "All India" button, Esc)
document.addEventListener("regionchange", refresh);
new ResizeObserver(() => { map.invalidateSize(); draw(); }).observe($(".mapcard"));
window.addEventListener("resize", draw);

async function setVar(key) {
  VAR = key; const V = VARS[key];
  document.querySelectorAll("#vars button").forEach(b => b.classList.toggle("on", b.dataset.v === key));
  $("#h1").textContent = document.title = `India ${V.title} trends`;
  $("#cnote").textContent = V.note + " Annual values compare each month with its long-term average, so years with a few missing months are still included (needs at least 6 months).";
  try {
    const d = await loadVar(key);
    if (VAR !== key) return; // switched again while loading
    selector = createTimePeriodSelector($("#tps"), { startYear: d.minYear, endYear: d.maxYear, defaultEnd: d.lastFull, onChange: refresh });
    refresh();
  } catch (e) {
    if (VAR !== key) return;
    last = null; selector = null; $("#chart").innerHTML = "";
    $("#gist").textContent = `Could not load ${V.title} data (${e.message}). Check that data/processed/regional_timeseries/${V.file}_state_monthly.csv exists and serve the project root with: python3 -m http.server 8080`;
    console.error(e);
  }
}
$("#vars").onclick = e => { const b = e.target.closest("button"); if (b && b.dataset.v !== VAR) setVar(b.dataset.v); };
setVar("t2m");
