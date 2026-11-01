/* FranklinWH System view: a full-page overlay over the bridge's own UI.
 *
 * The bridge serves this file and system-view.css at /system-view/, includes both, and
 * calls FWHSystemView.mount({endpoint: "/api/system"}). Nothing else in the bridge's UI
 * changes. The layout arrives precomputed (franklinwh_system_view.layout); this file only
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
    gen: '<rect x="5" y="10" width="38" height="26" rx="3"/><path d="M26 14 L19 24 H25 L22 32 L29 22 H23 Z"/><circle cx="13" cy="40" r="3"/><circle cx="35" cy="40" r="3"/>'
  };
  const PORTRAIT_BELOW = 640;
  const POLL_MS = 5000;
  const KEY_START = "fwh-system-view:start";

  let opts = { endpoint: "/api/system", title: "System view", backLabel: "Standard dashboard" };
  let root, svg, panel, tip, chips, startBox, lastFocus, timer, data = null, gwIdx = 0, sel = null;
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
      '<label class="fwhsv-start"><input type="checkbox"> Start on ' + esc(opts.title) + '</label>' +
      '<button type="button" class="fwhsv-close">' + esc(opts.backLabel) + ' ✕</button></div>' +
      '<div class="fwhsv-body"><div class="fwhsv-stage"><svg class="fwhsv-svg" role="group" aria-label="System diagram"></svg>' +
      '<p class="fwhsv-empty" hidden></p></div>' +
      '<aside class="fwhsv-panel" hidden aria-live="polite"></aside></div>' +
      '<div class="fwhsv-tip" hidden></div>';
    document.body.appendChild(root);
    svg = root.querySelector("svg");
    panel = root.querySelector(".fwhsv-panel");
    tip = root.querySelector(".fwhsv-tip");
    chips = root.querySelector(".fwhsv-chips");
    startBox = root.querySelector(".fwhsv-start input");
    startBox.checked = store.get(KEY_START) === "1";
    startBox.addEventListener("change", () => store.set(KEY_START, startBox.checked ? "1" : null));
    root.querySelector(".fwhsv-close").addEventListener("click", () => close());
    root.querySelector(".fwhsv-zoom").addEventListener("click", (e) => {
      const z = e.target.closest("button") && e.target.closest("button").dataset.z;
      if (z === "in") setZoom(zoom * 1.25);
      else if (z === "out") setZoom(zoom / 1.25);
      else if (z === "fit") { zoom = 1; panX = panY = 0; applyView(); }
    });
    root.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
    wirePointer();
    window.addEventListener("resize", () => { if (!root.hidden) draw(); });
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
        s += `<text class="fwhsv-soc" x="${n.x + 48}" y="${ry + 6}">${Math.round(n.soc)}%</text>`;
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
    chips.innerHTML = gws.length > 1 ? gws.map((g, i) =>
      `<button type="button" role="tab" aria-selected="${i === gwIdx}" data-i="${i}" class="s-${g.online ? "ok" : "off"}">${esc(g.name)}</button>`).join("") : "";
    chips.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { gwIdx = +b.dataset.i; sel = null; zoom = 1; draw(); }));
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
      el.addEventListener("pointerenter", (e) => showTip(n, e.clientX, e.clientY));
      el.addEventListener("pointermove", (e) => showTip(n, e.clientX, e.clientY));
      el.addEventListener("pointerleave", () => { tip.hidden = true; });
      el.addEventListener("focus", () => { const r = el.getBoundingClientRect(); showTip(n, r.left + r.width / 2, r.bottom); });
      el.addEventListener("blur", () => { tip.hidden = true; });
    });
    if (sel) { const n = scn.nodes.find((x) => x.id === sel); n ? showPanel(n) : (panel.hidden = true); }
  }
  function showTip(n, x, y) {
    tip.innerHTML = `<b>${esc(n.label)}</b><br>${esc(n.hover)}`;
    tip.hidden = false;
    const w = tip.offsetWidth, vw = window.innerWidth;
    tip.style.left = Math.max(8, Math.min(vw - w - 8, x + 14)) + "px";
    tip.style.top = (y + 14) + "px";
  }
  function showPanel(n) {
    panel.hidden = false;
    panel.innerHTML = `<button type="button" class="fwhsv-pclose" aria-label="Close details">✕</button>` +
      `<h3>${esc(n.label)}</h3><p>${esc(n.hover)}</p>` +
      `<dl>${n.rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>`;
    panel.querySelector(".fwhsv-pclose").addEventListener("click", () => { sel = null; panel.hidden = true; draw(); });
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
    root.hidden = false;
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

  window.FWHSystemView = { mount, open: () => open(), close: () => close(), _icons: IC };
})();
