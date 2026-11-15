// Dashboard: time-period selector, regression stats, gist, articles, trend chart.
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const $ = s => document.querySelector(s);

/* ---------- reusable time period selector ---------- */
function createTimePeriodSelector(root, { startYear = 1980, endYear = 2025, onChange = () => {} } = {}) {
  const yrs = id => `<select id="${id}">` + Array.from({ length: endYear - startYear + 1 }, (_, i) => endYear - i).map(y => `<option>${y}</option>`).join("") + "</select>";
  root.innerHTML = `
    <div class="seg">
      <button data-m="range" class="on">Year range</button><button data-m="ym">Year &amp; months</button><button data-m="one">Single month</button></div>
    <div class="ctl on" data-c="range">${yrs("ya")}<span class="to">to</span>${yrs("yb")}</div>
    <div class="ctl" data-c="ym">${yrs("yc")}<div class="chips">${MONTHS.map((m, i) => `<label><input type="checkbox" value="${i}"><span>${m}</span></label>`).join("")}</div></div>
    <div class="ctl" data-c="one">${yrs("yd")}<select id="mo">${MONTHS.map((m, i) => `<option value="${i}">${m}</option>`).join("")}</select></div>`;
  const q = s => root.querySelector(s);
  q("#ya").value = startYear; q("#yb").value = endYear; q("#yc").value = endYear; q("#yd").value = endYear;
  let mode = "range";
  const get = () => ({
    mode, a: +q("#ya").value, b: +q("#yb").value, year: +q(mode === "ym" ? "#yc" : "#yd").value,
    months: [...root.querySelectorAll(".chips input:checked")].map(c => +c.value), month: +q("#mo").value
  });
  root.querySelectorAll(".seg button").forEach(b => b.onclick = () => {
    mode = b.dataset.m;
    root.querySelectorAll(".seg button").forEach(x => x.classList.toggle("on", x === b));
    root.querySelectorAll(".ctl").forEach(c => c.classList.toggle("on", c.dataset.c === mode));
    onChange(get());
  });
  root.addEventListener("change", () => onChange(get()));
  return { get };
}

/* ---------- demo data (replace with real data) ---------- */
function hash(s) { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
function rnd(s) { let a = hash(s); a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function monthTemp(r, y, m) {
  const base = 18 + rnd(r + "b") * 10, trend = 0.012 + rnd(r + "t") * 0.04, amp = 3 + rnd(r + "a") * 6;
  return base + trend * (y - 1980) + amp * Math.cos(2 * Math.PI * (m - 5) / 12) + (rnd(`${r}${y}-${m}`) - .5) * 1.6;
}
function getSeries(r, p) {
  if (p.mode === "range") {
    const a = Math.min(p.a, p.b), b = Math.max(p.a, p.b), pts = [];
    for (let y = a; y <= b; y++) pts.push({ x: y, label: y, y: MONTHS.reduce((s, _, m) => s + monthTemp(r, y, m), 0) / 12 });
    return { pts, scale: 10, unit: "per decade", span: `${a}–${b}`, xl: "Year" };
  }
  if (p.mode === "ym") {
    const ms = p.months.length ? p.months : MONTHS.map((_, i) => i);
    return { pts: ms.sort((a, b) => a - b).map(m => ({ x: m, label: MONTHS[m] + " " + p.year, y: monthTemp(r, p.year, m) })),
      scale: 1, unit: "per month", span: `${p.year}${p.months.length ? " (" + ms.map(m => MONTHS[m]).join(", ") + ")" : ""}`, xl: "Month" };
  }
  const n = new Date(p.year, p.month + 1, 0).getDate(), base = monthTemp(r, p.year, p.month), pts = [];
  for (let d = 1; d <= n; d++) pts.push({ x: d, label: `${d} ${MONTHS[p.month]} ${p.year}`, y: base + (rnd(`${r}${p.year}${p.month}d${d}`) - .5) * 4 });
  return { pts, scale: 1, unit: "per day", span: `${MONTHS[p.month]} ${p.year}`, xl: "Day" };
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
function regress(pts) {
  const n = pts.length, x0 = pts[0].x, xs = pts.map(p => p.x - x0), ys = pts.map(p => p.y);
  const mx = xs.reduce((a, b) => a + b) / n, my = ys.reduce((a, b) => a + b) / n;
  let sxx = 0, sxy = 0; xs.forEach((x, i) => { sxx += (x - mx) ** 2; sxy += (x - mx) * (ys[i] - my); });
  const b = n > 1 && sxx ? sxy / sxx : 0, a = my - b * mx;
  let sse = 0; xs.forEach((x, i) => sse += (ys[i] - a - b * x) ** 2);
  const df = n - 2, se = df > 0 && sxx ? Math.sqrt(sse / df / sxx) : 0, t = se ? b / se : 0;
  return { b, a, x0, p: df > 0 && se ? betai(df / 2, .5, df / (df + t * t)) : 1, change: b * (xs[n - 1] - xs[0]) };
}

/* ---------- rendering ---------- */
const ARTICLES = [
  ["Why India's heat waves are arriving earlier", "Sample article · Climate desk"],
  ["Reading a temperature trend: slope, p-value and what they mean", "Sample article · Explainer"],
  ["Urban heat islands and regional warming", "Sample article · Research brief"]];
const region = () => (typeof selected !== "undefined" && selected) ? selected : "India";
const fmt = (v, d = 2) => (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(d);
let selector, last;

function refresh() {
  const r = region(), p = selector.get(), s = getSeries(r, p);
  if (s.pts.length < 3) { $("#gist").textContent = "Pick at least three data points to compute a trend."; return; }
  const st = regress(s.pts), sig = st.p < 0.05;
  $("#region").textContent = r;
  $("#change").className = "big " + (st.change > 0 ? "up" : "");
  $("#change").innerHTML = `${fmt(st.change)}<small>°C over ${s.span}</small>`;
  $("#pv").textContent = st.p < 0.001 ? "< 0.001" : st.p.toFixed(3);
  $("#sl").textContent = fmt(st.b * s.scale, 3) + " °C";
  $("#slu").textContent = "Slope " + s.unit;
  $("#ic").textContent = st.a.toFixed(1) + " °C";
  $("#gist").textContent = `${r} ${st.change >= 0 ? "warmed" : "cooled"} by about ${Math.abs(st.change).toFixed(2)} °C across ${s.span}, a rate of ${fmt(st.b * s.scale, 3)} °C ${s.unit}. ` +
    (sig ? "The trend is statistically significant (p < 0.05), so it is unlikely to be random variation." : "The trend is not statistically significant (p ≥ 0.05), so this change could be natural variability.");
  $("#arts").innerHTML = ARTICLES.map(a => `<li><a href="#">${a[0]}</a><small>${a[1]}</small></li>`).join("");
  $("#ctitle").textContent = "Temperature trend";
  $("#csub").textContent = `${r} · ${s.span}`;
  last = { s, st }; draw();
}

function draw() {
  if (!last) return;
  const { s, st } = last, el = $("#chart"), W = el.clientWidth || 800, H = 300, m = { l: 46, r: 14, t: 12, b: 30 };
  const xs = s.pts.map(p => p.x), ys = s.pts.map(p => p.y);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), yl = Math.min(...ys), yh = Math.max(...ys), pad = (yh - yl) * .12 || 1;
  const y0 = yl - pad, y1 = yh + pad, X = x => m.l + (x - x0) / (x1 - x0 || 1) * (W - m.l - m.r), Y = y => H - m.b - (y - y0) / (y1 - y0) * (H - m.t - m.b);
  const line = s.pts.map((p, i) => (i ? "L" : "M") + X(p.x).toFixed(1) + " " + Y(p.y).toFixed(1)).join("");
  const fit = v => st.a + st.b * (v - st.x0);
  let g = "";
  for (let i = 0; i <= 4; i++) { const v = y0 + (y1 - y0) * i / 4; g += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e4e8e7"/><text x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end" font-size="11.5" fill="#6c7776">${v.toFixed(1)}°</text>`; }
  const tk = Math.min(7, s.pts.length);
  for (let i = 0; i < tk; i++) { const p = s.pts[Math.round(i * (s.pts.length - 1) / (tk - 1 || 1))]; g += `<text x="${X(p.x)}" y="${H - 8}" text-anchor="middle" font-size="11.5" fill="#6c7776">${s.xl === "Month" ? MONTHS[p.x] : p.x}</text>`; }
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" height="${H}">${g}
    <path d="${line}" fill="none" stroke="#3454d1" stroke-width="2.2" stroke-linejoin="round"/>
    <line x1="${X(x0)}" y1="${Y(fit(x0))}" x2="${X(x1)}" y2="${Y(fit(x1))}" stroke="#16201f" stroke-width="1.6" stroke-dasharray="5 5"/>
    <circle id="dot" r="5" fill="#3454d1" stroke="#fff" stroke-width="2" style="display:none"/></svg><div class="tip"></div>`;
  const svg = el.querySelector("svg"), dot = el.querySelector("#dot"), tip = el.querySelector(".tip");
  svg.onmousemove = e => {
    const bx = svg.getBoundingClientRect(), mx = (e.clientX - bx.left) * W / bx.width;
    const p = s.pts.reduce((a, b) => Math.abs(X(b.x) - mx) < Math.abs(X(a.x) - mx) ? b : a);
    dot.style.display = ""; dot.setAttribute("cx", X(p.x)); dot.setAttribute("cy", Y(p.y));
    tip.textContent = `${p.label}: ${p.y.toFixed(2)} °C`; tip.style.left = X(p.x) * bx.width / W + "px"; tip.style.top = Y(p.y) * bx.width / W + "px"; tip.style.opacity = 1;
  };
  svg.onmouseleave = () => { dot.style.display = "none"; tip.style.opacity = 0; };
}

/* ---------- wire up ---------- */
selector = createTimePeriodSelector($("#tps"), { startYear: 1980, endYear: 2025, onChange: refresh });
// refresh whenever the map selection changes
const _sel = window.selectState, _reset = window.resetView;
window.selectState = function (n) { _sel(n); refresh(); };
window.resetView = function () { _reset(); if (selector) refresh(); };
// keep the map and chart sized to their boxes
new ResizeObserver(() => { map.invalidateSize(); draw(); }).observe($(".mapcard"));
window.addEventListener("resize", draw);
refresh();
