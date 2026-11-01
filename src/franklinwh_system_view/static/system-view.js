/* FranklinWH System view: a full-page overlay over the bridge's own UI.
 *
 * The bridge serves this file and system-view.css at /system-view/, includes both, and
 * calls FWHSystemView.mount({endpoint: "/api/system"}). Nothing else in the bridge's UI
 * changes. A host with its own gateway picker passes gateway (the id, or a function giving
 * it, read on open) and onGateway(id), called when the user picks a gateway here, and calls
 * FWHSystemView.showGateway(id) when its picker changes. The layout arrives precomputed (franklinwh_system_view.layout); this file only
 * draws it, and handles zoom, hover, the detail panel and opening/closing.
 */
(function () {
  "use strict";

  const IC = {
    pylon: '<path d="M24 4 L16 44 M24 4 L32 44 M11 12 H37 M9 20 H39 M18.5 32 H29.5 M17 20 L30 32 M31 20 L18 32 M14 12 L24 20 L34 12 M15 44 H33"/>',
    gridout: '<path d="M24 4 L16 44 M24 4 L32 44 M11 12 H37 M9 20 H39 M18.5 32 H29.5"/><path d="M6 6 L42 42" stroke-width="3.4"/>',
    gridspike: '<path d="M3 28 H12 L16 28 L20 6 L25 42 L29 28 H45"/><path d="M36 8 L40 16 H32 Z"/>',
    house: '<path d="M6 22 L24 6 L42 22 M10 19 V42 H38 V19 M20 42 V30 H28 V42"/>',
    solar: '<path d="M8 10 H40 L44 32 H4 Z M6 21 H42 M18 10 L16 32 M30 10 L32 32 M24 32 V40 M14 40 H34"/>',
    battery: '<rect x="11" y="8" width="26" height="36" rx="4"/><path d="M19 4.5 H29"/><rect class="f" x="15.5" y="26" width="17" height="14" rx="1.5"/><rect class="f" x="15.5" y="20" width="17" height="4" rx="1.5" opacity="0.55"/><path d="M25.5 11 L21 17 H27 L22.5 23" stroke-width="2"/>',
    apower: '<rect x="12" y="4" width="24" height="40" rx="5"/><path d="M12 14 H36 M12 34 H36"/><path d="M25 18 L21 25 H27 L23 31"/>',
    toggle: '<rect x="5" y="15" width="38" height="18" rx="9"/><circle class="f" cx="34" cy="24" r="5.5"/>',
    toggleoff: '<rect x="5" y="15" width="38" height="18" rx="9"/><circle cx="14" cy="24" r="5"/>',
    gen: '<rect x="5" y="10" width="38" height="26" rx="3"/><path d="M26 14 L19 24 H25 L22 32 L29 22 H23 Z"/><circle cx="13" cy="40" r="3"/><circle cx="35" cy="40" r="3"/>',
    // smart-circuit appliances (the user's choice in Customise diagram)
    hvac: '<rect x="5" y="10" width="38" height="20" rx="3"/><path d="M10 24 H38 M14 36 L12 42 M24 36 V42 M34 36 L36 42"/>',
    water: '<path d="M24 5 C16 16 11 23 11 30 A13 13 0 0 0 37 30 C37 23 32 16 24 5 Z"/><path d="M18 31 A6 6 0 0 0 24 37"/>',
    ev: '<path d="M8 30 L12 18 H36 L40 30 V38 H8 Z M8 30 H40"/><circle cx="15" cy="38" r="3"/><circle cx="33" cy="38" r="3"/><path d="M25 6 L21 13 H27 L23 20" stroke-width="2"/>',
    pool: '<path d="M4 30 Q10 26 16 30 T28 30 T40 30 T46 30 M4 38 Q10 34 16 38 T28 38 T40 38 T46 38 M16 26 V8 H24 M30 26 V8 H38"/>',
    other: '<path d="M18 6 V16 M30 6 V16 M12 16 H36 V24 A12 12 0 0 1 12 24 Z M24 36 V44"/>',
    // weather (WMO code mapped in Python: layout.weather_icon)
    sun: '<circle cx="24" cy="24" r="8"/><path d="M24 4 V9 M24 39 V44 M4 24 H9 M39 24 H44 M10 10 L13.5 13.5 M34.5 34.5 L38 38 M10 38 L13.5 34.5 M34.5 13.5 L38 10"/>',
    partcloud: '<circle cx="18" cy="17" r="7"/><path d="M18 4 V6 M5 17 H7 M8.5 7.5 L10 9 M27.5 7.5 L26 9"/><path d="M16 40 H36 A7 7 0 0 0 35 26 A10 10 0 0 0 16 28 A6 6 0 0 0 16 40 Z"/>',
    cloud: '<path d="M14 38 H36 A8 8 0 0 0 35 22 A12 12 0 0 0 12 25 A7 7 0 0 0 14 38 Z"/>',
    fog: '<path d="M14 26 H36 A8 8 0 0 0 35 12 A11 11 0 0 0 13 15 A6 6 0 0 0 14 26 Z M8 33 H40 M12 40 H36"/>',
    rainlight: '<path d="M14 30 H36 A8 8 0 0 0 35 14 A12 12 0 0 0 12 17 A7 7 0 0 0 14 30 Z M24 35 L22 41"/>',
    rain: '<path d="M14 30 H36 A8 8 0 0 0 35 14 A12 12 0 0 0 12 17 A7 7 0 0 0 14 30 Z M18 35 L16 41 M28 35 L26 41"/>',
    rainheavy: '<path d="M14 28 H36 A8 8 0 0 0 35 12 A12 12 0 0 0 12 15 A7 7 0 0 0 14 28 Z M15 33 L12 42 M24 33 L21 42 M33 33 L30 42"/>',
    snow: '<path d="M14 28 H36 A8 8 0 0 0 35 12 A12 12 0 0 0 12 15 A7 7 0 0 0 14 28 Z M17 36 H21 M19 34 V38 M27 38 H31 M29 36 V40"/>',
    storm: '<path d="M14 28 H36 A8 8 0 0 0 35 12 A12 12 0 0 0 12 15 A7 7 0 0 0 14 28 Z M25 30 L20 38 H27 L23 45"/>'
  };
  const PORTRAIT_BELOW = 640;
  const POLL_MS = 5000;
  const KEY_START = "fwh-system-view:start";

  // below / above: CSS selectors for the host's top bar and bottom bar (e.g. a phone tab
  // bar). The overlay fits between them, so the host's bars stay visible and usable.
  // gateway / onGateway: keep the shown gateway and the host's gateway picker the same.
  let opts = { endpoint: "/api/system", title: "System view", backLabel: "Standard dashboard", below: null, above: null,
               gateway: null, onGateway: null };
  let root, svg, panel, tip, chips, startBox, siteEl, custBtn, dlg, lastFocus, timer, data = null, gwIdx = 0, sel = null;
  let want = null;   // a gateway id to show once it is in the data
  let zoom = 1, panX = 0, panY = 0, scn = null;

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  };

  function build() {
    root = document.createElement("div");
    root.className = "fwhsv";
    root.hidden = true;
    root.setAttribute("role", "dialog");
    root.setAttribute("aria-modal", "true");
    root.setAttribute("aria-label", opts.title);
    root.innerHTML =
      '<div class="fwhsv-bar">' +
      '<strong class="fwhsv-title">' + esc(opts.title) + '</strong>' +
      '<div class="fwhsv-chips" role="tablist" aria-label="Gateways"></div>' +
      '<div class="fwhsv-zoom" role="group" aria-label="Zoom">' +
      '<button type="button" data-z="out" aria-label="Zoom out">−</button>' +
      '<button type="button" data-z="fit" aria-label="Fit to screen">Fit</button>' +
      '<button type="button" data-z="in" aria-label="Zoom in">+</button></div>' +
      '<button type="button" class="fwhsv-cust" hidden>Customise diagram</button>' +
      '<label class="fwhsv-start"><input type="checkbox"> Start on ' + esc(opts.title) + '</label>' +
      '<button type="button" class="fwhsv-close">' + esc(opts.backLabel) + ' ✕</button></div>' +
      '<div class="fwhsv-site" hidden></div>' +
      '<div class="fwhsv-body"><div class="fwhsv-stage"><svg class="fwhsv-svg" role="group" aria-label="System diagram"></svg>' +
      '<p class="fwhsv-empty" hidden></p></div>' +
      '<aside class="fwhsv-panel" hidden aria-live="polite"></aside></div>' +
      '<div class="fwhsv-tip" hidden></div>' +
      '<div class="fwhsv-dlg" hidden role="dialog" aria-modal="true" aria-label="Customise diagram"><form class="fwhsv-form"></form></div>';
    document.body.appendChild(root);
    svg = root.querySelector("svg");
    panel = root.querySelector(".fwhsv-panel");
    tip = root.querySelector(".fwhsv-tip");
    chips = root.querySelector(".fwhsv-chips");
    startBox = root.querySelector(".fwhsv-start input");
    siteEl = root.querySelector(".fwhsv-site");
    custBtn = root.querySelector(".fwhsv-cust");
    dlg = root.querySelector(".fwhsv-dlg");
    custBtn.addEventListener("click", openCustomise);
    startBox.checked = store.get(KEY_START) === "1";
    startBox.addEventListener("change", () => store.set(KEY_START, startBox.checked ? "1" : null));
    root.querySelector(".fwhsv-close").addEventListener("click", () => close());
    root.querySelector(".fwhsv-zoom").addEventListener("click", (e) => {
      const z = e.target.closest("button") && e.target.closest("button").dataset.z;
      if (z === "in") setZoom(zoom * 1.25);
      else if (z === "out") setZoom(zoom / 1.25);
      else if (z === "fit") { zoom = 1; panX = panY = 0; applyView(); }
    });
    root.addEventListener("keydown", (e) => { if (e.key === "Escape") dlg.hidden ? close() : closeCustomise(); });
    wirePointer();
    window.addEventListener("resize", () => { if (!root.hidden) { placeBelow(); draw(); } });
  }

  function placeBelow() {
    const el = opts.below && document.querySelector(opts.below);
    const b = el ? Math.max(0, Math.round(el.getBoundingClientRect().bottom)) : 0;
    root.style.top = b + "px";
    const f = opts.above && document.querySelector(opts.above);
    const fr = f ? f.getBoundingClientRect() : null;      // display:none gives height 0
    root.style.bottom = (fr && fr.height ? Math.max(0, Math.round(window.innerHeight - fr.top)) : 0) + "px";
  }

  /* ── zoom and pan: the viewBox shrinks around the centre; drag or pinch to move ── */
  function setZoom(z) { zoom = Math.max(1, Math.min(4, z)); if (zoom === 1) panX = panY = 0; applyView(); }
  function applyView() {
    if (!scn) return;
    const w = scn.width / zoom, h = scn.height / zoom;
    const maxX = scn.width - w, maxY = scn.height - h;
    panX = Math.max(0, Math.min(maxX, panX || maxX / 2));
    panY = Math.max(0, Math.min(maxY, panY || maxY / 2));
    if (zoom === 1) panX = panY = 0;
    svg.setAttribute("viewBox", `${panX} ${panY} ${w} ${h}`);
  }
  function wirePointer() {
    const pts = new Map();
    let pinch0 = 0, zoom0 = 1, drag = null;
    svg.addEventListener("pointerdown", (e) => {
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch0 = Math.hypot(a.x - b.x, a.y - b.y); zoom0 = zoom; }
      else if (zoom > 1) drag = { x: e.clientX, y: e.clientY, px: panX, py: panY };
    });
    svg.addEventListener("pointermove", (e) => {
      if (!pts.has(e.pointerId)) return;
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pts.size === 2 && pinch0) {
        const [a, b] = [...pts.values()];
        setZoom(zoom0 * Math.hypot(a.x - b.x, a.y - b.y) / pinch0);
      } else if (drag) {
        const r = svg.getBoundingClientRect(), k = scn.width / zoom / r.width;
        panX = drag.px - (e.clientX - drag.x) * k; panY = drag.py - (e.clientY - drag.y) * k;
        applyView();
      }
    });
    const end = (e) => { pts.delete(e.pointerId); if (pts.size < 2) pinch0 = 0; if (!pts.size) drag = null; };
    svg.addEventListener("pointerup", end);
    svg.addEventListener("pointercancel", end);
    svg.addEventListener("wheel", (e) => { if (!e.ctrlKey) return; e.preventDefault(); setZoom(zoom * (e.deltaY < 0 ? 1.1 : 1 / 1.1)); }, { passive: false });
  }

  /* ── drawing ── */
  function icon(k, x, y, s) {
    return `<g transform="translate(${x},${y}) scale(${s / 48})"><g class="fwhsv-ic">${IC[k] || ""}</g></g>`;
  }
  function nodeSvg(n) {
    const cx = n.x + n.w / 2, cls = `fwhsv-obj s-${n.state}` + (n.frame ? "" : " noframe") + (sel === n.id ? " sel" : "");
    let s = `<g class="${cls}" tabindex="0" role="button" data-id="${esc(n.id)}" aria-label="${esc(n.label)}: ${esc(n.hover)}">`;
    if (n.card) {      // battery card
      const r = 28, c = 2 * Math.PI * r, f = c * (n.soc || 0) / 100, ry = n.y + n.h / 2;
      s += `<rect class="fwhsv-frame" x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="14"/>`;
      if (n.soc !== null && n.soc !== undefined) {
        s += `<circle class="fwhsv-ring0" cx="${n.x + 48}" cy="${ry}" r="${r}"/><circle class="fwhsv-ring" cx="${n.x + 48}" cy="${ry}" r="${r}" stroke-dasharray="${f} ${c}" transform="rotate(-90 ${n.x + 48} ${ry})"/>`;
        const pct = Math.round(n.soc);     // three digits need a smaller size to stay inside the ring
        s += `<text class="fwhsv-soc${pct >= 100 ? " w3" : ""}" x="${n.x + 48}" y="${ry + 6}">${pct}%</text>`;
      } else s += icon("apower", n.x + 24, ry - 24, 48);
      s += `<text class="fwhsv-lbl start" x="${n.x + 92}" y="${ry - 8}">${esc(n.label)}</text>`;
      s += `<text class="fwhsv-st start" x="${n.x + 92}" y="${ry + 16}">${esc(n.status)}${n.value ? " · " + esc(n.value) : ""}</text>`;
      return s + "</g>";
    }
    s += `<rect class="fwhsv-hit" x="${n.x - 6}" y="${n.y - 6}" width="${n.w + 12}" height="${n.foot + 12}" rx="12"/>`;
    if (n.frame) s += `<rect class="fwhsv-frame" x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="16"/>`;
    const is = Math.min(n.w, n.h) * (n.frame ? 0.5 : 0.75);
    s += icon(n.icon, cx - is / 2, n.y + (n.h - is) / 2, is);
    let ty = n.y + n.h + 20;
    s += `<text class="fwhsv-lbl" x="${cx}" y="${ty}">${esc(n.label)}</text>`;
    if (n.value) { ty += 24; s += `<text class="fwhsv-big" x="${cx}" y="${ty}">${esc(n.value)}</text>`; }
    ty += 18; s += `<text class="fwhsv-st" x="${cx}" y="${ty}">${esc(n.status)}</text>`;
    if (n.sub) { ty += 16; s += `<text class="fwhsv-sub" x="${cx}" y="${ty}">${esc(n.sub)}</text>`; }
    return s + "</g>";
  }
  function draw() {
    if (!data) return;
    const empty = root.querySelector(".fwhsv-empty");
    const gws = data.gateways || [];
    if (want != null) {
      const i = gws.findIndex((g) => g.id === want);
      if (i >= 0 && i !== gwIdx) { gwIdx = i; sel = null; zoom = 1; }
      want = null;
    }
    drawStrip();
    custBtn.hidden = !data.customise;
    chips.innerHTML = gws.length > 1 ? gws.map((g, i) =>
      `<button type="button" role="tab" aria-selected="${i === gwIdx}" data-i="${i}" class="s-${g.online ? "ok" : "off"}">${esc(g.name)}</button>`).join("") : "";
    chips.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      gwIdx = +b.dataset.i; sel = null; zoom = 1; draw();
      if (opts.onGateway) opts.onGateway(gws[gwIdx].id);
    }));
    if (!gws.length) {
      svg.innerHTML = ""; empty.hidden = false;
      empty.textContent = "No gateways yet. Add one in Settings › Gateways and it will appear here.";
      return;
    }
    empty.hidden = true;
    const g = gws[Math.min(gwIdx, gws.length - 1)];
    const portrait = root.querySelector(".fwhsv-stage").clientWidth < PORTRAIT_BELOW;
    scn = g.scenes[portrait ? "portrait" : "landscape"];
    const wires = scn.wires.map((w) => `<path class="fwhsv-wire ${w.flow}${w.dc ? " dc" : ""}" d="${w.d}"/>`).join("");
    svg.innerHTML = wires + scn.nodes.map(nodeSvg).join("");
    applyView();
    svg.querySelectorAll(".fwhsv-obj").forEach((el) => {
      const n = scn.nodes.find((x) => x.id === el.dataset.id);
      const pick = () => { sel = n.id; showPanel(n); draw(); };
      el.addEventListener("click", pick);
      el.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } });
      // No hover tip for a touch: the tap opens the details, which say the same, and a
      // tip left behind by a tap covered the details' ✕ (iOS sends no pointerleave).
      el.addEventListener("pointerenter", (e) => { if (e.pointerType !== "touch") showTip(n, e.clientX, e.clientY); });
      el.addEventListener("pointermove", (e) => { if (e.pointerType !== "touch") showTip(n, e.clientX, e.clientY); });
      el.addEventListener("pointerleave", () => { tip.hidden = true; });
      el.addEventListener("focus", () => { const r = el.getBoundingClientRect(); showTip(n, r.left + r.width / 2, r.bottom); });
      el.addEventListener("blur", () => { tip.hidden = true; });
    });
    if (sel) { const n = scn.nodes.find((x) => x.id === sel); n ? showPanel(n) : (panel.hidden = true); }
  }
  function showTip(n, x, y) {
    tip.innerHTML = `<b>${esc(n.label)}</b><br>${esc(n.hover)}`;
    tip.hidden = false;
    // Above the pointer, so the tip never covers the label and value under the picture;
    // below it only when there's no room above.
    const w = tip.offsetWidth, h = tip.offsetHeight, vw = window.innerWidth;
    tip.style.left = Math.max(8, Math.min(vw - w - 8, x + 14)) + "px";
    tip.style.top = (y - h - 14 >= 8 ? y - h - 14 : y + 18) + "px";
  }
  function showPanel(n) {
    tip.hidden = true;
    panel.hidden = false;
    panel.innerHTML = `<button type="button" class="fwhsv-pclose" aria-label="Close details">✕</button>` +
      `<h3>${esc(n.label)}</h3><p>${esc(n.hover)}</p>` +
      `<dl>${n.rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>`;
    panel.querySelector(".fwhsv-pclose").addEventListener("click", () => { sel = null; panel.hidden = true; draw(); });
  }

  /* ── site strip: name and weather ── */
  function drawStrip() {
    const st = data.strip || {};
    if (!st.name && !st.weather) { siteEl.hidden = true; return; }
    siteEl.hidden = false;
    let h = st.name ? `<strong>${esc(st.name)}</strong>` : "";
    if (st.weather) {
      h += `<span class="fwhsv-wx" tabindex="0" title="${esc(st.weather.hover)}"><svg viewBox="0 0 48 48" aria-hidden="true"><g class="fwhsv-ic">${IC[st.weather.icon] || ""}</g></svg>${esc(st.weather.text)}</span>`;
    }
    siteEl.innerHTML = h;
  }

  /* ── Customise diagram: the bridge's own settings, saved in the bridge ── */
  function fieldHtml(f, i) {
    const id = "fwhsv-f" + i, auto = f.auto != null && f.auto !== "" ? String(f.auto) : null;
    let ctl;
    if (f.type === "choice") {
      ctl = `<select id="${id}" data-i="${i}">` + f.choices.map(([v, l]) =>
        `<option value="${esc(v)}"${String(f.value == null ? "" : f.value) === String(v) ? " selected" : ""}>${esc(l)}</option>`).join("") + "</select>";
    } else {
      ctl = `<input id="${id}" data-i="${i}" type="text" value="${esc(f.value || "")}" placeholder="${esc(f.placeholder || auto || "")}">`;
    }
    let note = f.help ? `<small>${esc(f.help)}</small>` : "";
    if (f.confirm) note += `<small class="fwhsv-confirm">Please confirm: this is a guess, not a reading.</small>`;
    if (f.mismatch) note += `<small class="fwhsv-mismatch">${esc(f.mismatch)}</small>`;
    return `<div class="fwhsv-field"><label for="${id}">${esc(f.label)}</label>${ctl}${note}</div>`;
  }
  function openCustomise() {
    const c = data && data.customise;
    if (!c) return;
    const fields = c.fields || [], groups = [];
    fields.forEach((f, i) => {
      let g = groups.find((x) => x.scope === f.scope);
      if (!g) groups.push(g = { scope: f.scope, title: f.group || f.scope, items: [] });
      g.items.push(fieldHtml(f, i));
    });
    const form = dlg.querySelector("form");
    form.innerHTML = `<h3>Customise diagram</h3><p class="fwhsv-intro">${esc(c.intro || "")}</p>` +
      groups.map((g) => `<fieldset><legend>${esc(g.title)}</legend>${g.items.join("")}</fieldset>`).join("") +
      `<p class="fwhsv-result" role="status" hidden></p>` +
      `<div class="fwhsv-actions"><button type="button" class="fwhsv-cancel">Close</button><button type="submit" class="fwhsv-save">Save</button></div>`;
    form.onsubmit = (e) => { e.preventDefault(); saveCustomise(fields); };
    form.querySelector(".fwhsv-cancel").onclick = closeCustomise;
    dlg.hidden = false;
    const first = form.querySelector("input, select");
    if (first) first.focus();
  }
  function closeCustomise() { dlg.hidden = true; custBtn.focus(); }
  async function saveCustomise(fields) {
    const form = dlg.querySelector("form"), out = dlg.querySelector(".fwhsv-result");
    const values = {};
    form.querySelectorAll("[data-i]").forEach((el) => {
      const f = fields[+el.dataset.i];
      (values[f.scope] = values[f.scope] || {})[f.key] = el.value.trim();
    });
    out.hidden = false; out.className = "fwhsv-result"; out.textContent = "Saving…";
    try {
      const r = await fetch(data.customise.endpoint, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(body.detail || ("HTTP " + r.status));
      await load();
      openCustomise();                 // redraw the form: readings and mismatches follow the answers
      const res = dlg.querySelector(".fwhsv-result");
      res.hidden = false; res.className = "fwhsv-result ok";
      res.textContent = "Saved. The diagram now uses these settings, in every browser.";
    } catch (e) {
      out.className = "fwhsv-result err";
      out.textContent = "Not saved: " + e.message;
    }
  }

  /* ── data ── */
  async function load() {
    try {
      const r = await fetch(opts.endpoint, { cache: "no-store" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      data = await r.json();
      draw();
    } catch (e) {
      const empty = root.querySelector(".fwhsv-empty");
      if (!data) { empty.hidden = false; empty.textContent = "Couldn't load the system view (" + e.message + "). It will retry."; }
    }
  }
  function poll() { clearInterval(timer); timer = setInterval(() => { if (!document.hidden) load(); }, POLL_MS); }

  /* ── open and close ── */
  function open(push) {
    if (!root) build();
    if (!root.hidden) return;
    lastFocus = document.activeElement;
    if (opts.gateway != null) want = typeof opts.gateway === "function" ? opts.gateway() : opts.gateway;
    root.hidden = false;
    placeBelow();
    document.documentElement.classList.add("fwhsv-open");
    if (push !== false && location.hash !== "#system") history.pushState({ fwhsv: 1 }, "", "#system");
    load(); poll();
    root.querySelector(".fwhsv-close").focus();
  }
  function close(fromHistory) {
    if (!root || root.hidden) return;
    root.hidden = true; tip.hidden = true;
    document.documentElement.classList.remove("fwhsv-open");
    clearInterval(timer);
    if (!fromHistory && location.hash === "#system") history.back();
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function mount(o) {
    opts = Object.assign(opts, o || {});
    window.addEventListener("popstate", () => { location.hash === "#system" ? open(false) : close(true); });
    if (location.hash === "#system" || store.get(KEY_START) === "1") open(location.hash !== "#system");
  }

  function showGateway(id) {
    want = id;
    if (data && root && !root.hidden) draw();
  }

  window.FWHSystemView = { mount, open: () => open(), close: () => close(), showGateway, _icons: IC };
})();
