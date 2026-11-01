"""Turn one gateway's payload into a scene: positioned pictures and the wires between them.

The layout is computed here, in Python, so both bridges draw the same picture and the
arrangement is tested without a browser. The page only renders the scene.

Two arrangements: ``landscape`` (desktop and tablet) and ``portrait`` (phones). Only what
the payload reports is drawn; a gateway with no solar has no solar picture.
"""
from __future__ import annotations

from typing import Any

#: Below this a flow is drawn idle, so meter noise doesn't animate a wire.
FLOW_W = 50
#: Batteries drawn one by one; more than this collapse into one "+N more" card.
MAX_UNITS = 4
MAX_SOLAR = 3
WHERE = {"agate": "aGate", "apbox": "aPbox", "apower": "aPower S (DC)", "ahub": "aHub port", "panel": "Panel"}


def kw(w: Any) -> str:
    return "–" if w is None else f"{abs(w) / 1000:.2f} kW"


def _flow(w: Any, *, reverse: bool = False) -> str:
    if w is None or abs(w) < FLOW_W:
        return "idle"
    forward = (w > 0) != reverse
    return "fwd" if forward else "rev"


def _node(id_, icon, x, y, w, h, label, *, value="", status="", state="ok", frame=True,
          hover="", rows=None, soc=None, card=False, sub="") -> dict:
    """``foot`` is the height including the text under the picture; wires leave below it."""
    foot = h if card else h + 22 + (24 if value else 0) + 18 + (16 if sub else 0) + 8
    n = {"id": id_, "icon": icon, "x": x, "y": y, "w": w, "h": h, "foot": foot, "label": label,
         "value": value, "status": status, "state": state, "frame": frame,
         "hover": hover, "rows": rows or [], "soc": soc, "card": card}
    if sub:
        n["sub"] = sub
    return n


def _wire(a: dict, b: dict, flow: str, *, dc: bool = False, side_a="c", side_b="c") -> dict:
    """An orthogonal wire from ``a`` to ``b``; ``flow`` "fwd" runs a→b, "rev" b→a."""
    def anchor(n, side):
        cx, cy = n["x"] + n["w"] / 2, n["y"] + n["h"] / 2
        return {"l": (n["x"], cy), "r": (n["x"] + n["w"], cy), "t": (cx, n["y"]),
                "b": (cx, n["y"] + n["foot"]), "c": (cx, cy)}[side]
    (x1, y1), (x2, y2) = anchor(a, side_a), anchor(b, side_b)
    if side_a in "lr" and side_b in "lr":
        mx = (x1 + x2) / 2
        d = f"M{x1:g} {y1:g} H{mx:g} V{y2:g} H{x2:g}"
    elif side_a in "tb" and side_b in "tb":
        my = (y1 + y2) / 2
        d = f"M{x1:g} {y1:g} V{my:g} H{x2:g} V{y2:g}"
    elif side_a in "lr":
        d = f"M{x1:g} {y1:g} H{x2:g} V{y2:g}"
    else:
        d = f"M{x1:g} {y1:g} V{y2:g} H{x2:g}"
    return {"from": a["id"], "to": b["id"], "d": d, "flow": flow, "dc": dc}


# ── the objects, independent of arrangement ──────────────────────────────────────

def _grid(g: dict) -> dict | None:
    grid = g.get("grid")
    if grid is None or "grid" in (g.get("unavailable") or []):
        return None
    st = grid.get("state", "unknown")
    p = grid.get("power_w")
    if st == "outage":
        return _with_legs({"icon": "gridout", "label": "Grid", "value": kw(0), "status": "Outage",
                           "state": "crit", "hover": "The grid is down. Your batteries are powering the backed-up circuits.",
                           "rows": [["State", "Outage"]], "flow": "off"}, g)
    word = ("Importing" if p and p >= FLOW_W else "Exporting" if p and p <= -FLOW_W else "Idle")
    rows = [["State", "Connected" if st != "unknown" else "Unknown"], ["Right now", f"{word} {kw(p)}" if word != "Idle" else "Idle"]]
    if grid.get("voltage_v") is not None:
        rows.append(["Voltage", f"{grid['voltage_v']:.1f} V"])
    if grid.get("freq_hz") is not None:
        rows.append(["Frequency", f"{grid['freq_hz']:.2f} Hz"])
    if st == "spike":
        return _with_legs({"icon": "gridspike", "label": "Grid", "value": kw(p), "status": "Voltage spike",
                           "state": "warn", "hover": "Your aGate reported a grid voltage spike. The grid is still connected.",
                           "rows": rows, "flow": _flow(p)}, g)
    hover = {"Importing": f"The grid is up. You are importing {kw(p)}.",
             "Exporting": f"The grid is up. You are exporting {kw(p)}.",
             "Idle": "The grid is up. Almost nothing is flowing to or from it right now."}[word]
    out = {"icon": "pylon", "label": "Grid", "value": kw(p), "status": "Connected" if st != "unknown" else "Unknown",
           "state": "ok" if st != "unknown" else "off", "hover": hover, "rows": rows, "flow": _flow(p)}
    return _with_legs(out, g)


def _with_legs(spec: dict, g: dict) -> dict:
    """The service legs this aGate is wired to, under the grid picture (a user setting)."""
    legs = g.get("legs")
    if legs:
        spec["sub"] = legs.replace("+", " + ")
        spec["rows"] = spec["rows"] + [["Service legs", spec["sub"]]]
    return spec


def _agate(g: dict) -> dict:
    mode, inv = g.get("mode"), g.get("inverter")
    online = g.get("online")
    rows = [["Mode", mode or "–"], ["Inverter", inv or "–"]]
    if g.get("reserve_pct") is not None:
        rows.append(["Backup reserve", f"{g['reserve_pct']:g} %"])
    if not online:
        return {"icon": "battery", "label": g.get("name") or "aGate", "status": "Offline", "state": "off",
                "hover": "The bridge can't reach this aGate right now.", "rows": rows}
    hover = f"Your aGate is in {mode}." if mode else "Your aGate is online."
    if mode == "Emergency Backup":
        hover += " The batteries are kept ready for an outage."
    if inv:
        hover += f" Inverter: {inv.lower()}."
    return {"icon": "battery", "label": g.get("name") or "aGate", "status": mode or "Online",
            "sub": inv or "", "state": "ok", "hover": hover, "rows": rows}


def _home(g: dict) -> dict | None:
    home = g.get("home")
    if home is None:
        return None
    p = home.get("power_w")
    return {"icon": "house", "label": "Home", "value": kw(p), "status": "Using", "state": "ok",
            "hover": f"Your home is using {kw(p)}.", "rows": [["Using now", kw(p)]], "flow": _flow(p)}


def _solars(g: dict) -> list[dict]:
    out = []
    arrays = g.get("solar") or []
    for i, s in enumerate(arrays[:MAX_SOLAR]):
        p = s.get("power_w")
        name = s.get("name") or ("Solar" if len(arrays) == 1 else f"Solar {i + 1}")
        producing = p is not None and p >= FLOW_W
        if p is None:       # drawn from Customise diagram; nothing reports its power
            status, hover = "Not reported", f"{name} is on your diagram, but nothing reports its power."
        elif producing:
            status, hover = "Producing", f"{name} is producing {kw(p)}."
        else:
            status, hover = "Not producing", f"{name} isn't producing right now."
        out.append({"id": s.get("id") or f"solar{i}", "icon": "solar", "label": name,
                    "value": kw(p) if p is not None else "", "status": status,
                    "state": "ok" if producing else "off", "hover": hover,
                    "rows": [["Now", kw(p)], ["Connected", WHERE.get(s.get("where"), "–")]],
                    "flow": _flow(p), "dc": s.get("where") == "apower"})
    return out


def _batteries(g: dict) -> list[dict]:
    bat = g.get("battery")
    if bat is None:
        return []
    units = bat.get("units") or []

    def card(id_, name, soc, p, state="ok"):
        soc = None if soc is None else round(soc)      # the ring, the sentence and the table agree
        word = "Discharging" if p and p >= FLOW_W else "Charging" if p and p <= -FLOW_W else "Idle"
        status = {"warn": "Warning", "crit": "Fault", "off": "Offline"}.get(state, word)
        hover = f"{name} is {soc:g} % full" if soc is not None else name
        hover += {"Discharging": f" and discharging {kw(p)}.", "Charging": f" and charging {kw(p)}.",
                  "Idle": " and idle."}.get(word, ".") if state == "ok" else f". {status}."
        return {"id": id_, "icon": "apower", "label": name, "value": kw(p) if word != "Idle" else "",
                "status": status, "state": state, "soc": soc, "hover": hover,
                "rows": [["Charge", "–" if soc is None else f"{soc:g} %"], ["Now", status if word == "Idle" or state != "ok" else f"{word} {kw(p)}"]],
                "flow": "off" if state == "off" else _flow(p, reverse=True)}

    if not units:
        n = bat.get("count")
        base = bat.get("model") or ("Batteries" if (n or 0) > 1 else "Battery")
        name = f"{base} ×{n}" if n and n > 1 else base
        c = card("battery", name, bat.get("soc_pct"), bat.get("power_w"))
        if bat.get("model"):
            c["rows"].append(["Model", bat["model"]])
        return [c]
    cards = [card(u.get("id") or f"bat{i}", u.get("name") or f"Battery {i + 1}", u.get("soc_pct"),
                  u.get("power_w"), u.get("state", "ok")) for i, u in enumerate(units)]
    if len(cards) > MAX_UNITS:
        rest = cards[MAX_UNITS - 1:]
        more = card("battery_more", f"+{len(rest)} more", None, sum(c_p for c_p in
                    (u.get("power_w") or 0 for u in units[MAX_UNITS - 1:])))
        more["hover"] = f"{len(rest)} more batteries. Open the Battery tab for each one."
        cards = cards[:MAX_UNITS - 1] + [more]
    return cards


def _circuits(g: dict) -> list[dict]:
    out = []
    for i, c in enumerate(g.get("circuits") or []):
        on = c.get("on")
        name = c.get("name") or f"Circuit {i + 1}"
        kind = c.get("icon") or "circuit"
        out.append({"id": f"sc{c.get('id', i + 1)}",
                    "icon": ("toggle" if on else "toggleoff") if kind == "circuit" else kind,
                    "label": name, "value": kw(c["power_w"]) if c.get("power_w") is not None else "",
                    "status": "On" if on else "Off" if on is False else "Unknown",
                    "state": "ok" if on else "off",
                    "hover": f"{name} is {'on' if on else 'off'}." if on is not None else f"{name}: state unknown.",
                    "rows": [["State", "On" if on else "Off"]], "flow": "fwd" if on else "idle"})
    return out


def _generator(g: dict) -> dict | None:
    gen = g.get("generator")
    if gen is None:
        return None
    p = gen.get("power_w")
    running = p is not None and p >= FLOW_W
    if p is None:
        return {"icon": "gen", "label": "Generator", "value": "", "status": "Not reported", "state": "off",
                "hover": "A generator is on your diagram, but nothing reports its power.",
                "rows": [["State", "Not reported"]], "flow": "idle"}
    return {"icon": "gen", "label": "Generator", "value": kw(p) if running else "",
            "status": "Running" if running else gen.get("status") or "Standby",
            "state": "ok" if running else "off",
            "hover": f"The generator is supplying {kw(p)}." if running else "The generator is on standby.",
            "rows": [["State", "Running" if running else "Standby"]], "flow": _flow(p)}


# ── the site strip: its name and the weather ─────────────────────────────────────

def weather_icon(code: Any) -> str | None:
    """A WMO weather code (Open-Meteo ``weather_code``) as one of the weather pictures."""
    if not isinstance(code, int):
        return None
    if code in (0, 1):
        return "sun"
    if code == 2:
        return "partcloud"
    if code == 3:
        return "cloud"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 56, 61, 80):
        return "rainlight"
    if code in (55, 57, 63, 66, 81):
        return "rain"
    if code in (65, 67, 82):
        return "rainheavy"
    if 71 <= code <= 77 or code in (85, 86):
        return "snow"
    if code >= 95:
        return "storm"
    return "cloud"


def strip(payload: dict) -> dict:
    """What sits above the diagram: the site's name and, when the bridge has it, the weather."""
    site = payload.get("site") or {}
    out: dict = {"name": site.get("name") or ""}
    w = site.get("weather")
    if w and weather_icon(w.get("code")):
        cond = w.get("condition") or ""
        temp = w.get("temp_c")
        text = cond + (f" · {temp:.0f} °C" if temp is not None else "")
        where = f" in {site['name']}" if site.get("name") else ""
        now = ", ".join(x for x in (cond.lower(), f"{temp:.0f} °C" if temp is not None else "") if x)
        out["weather"] = {"icon": weather_icon(w["code"]), "text": text.strip(" ·"),
                          "hover": f"Weather{where} now: {now}. From Open-Meteo."}
    return out


# ── arrangements ──────────────────────────────────────────────────────────────

def _place(spec: dict | None, id_, x, y, w, h, *, frame=True, card=False) -> dict | None:
    if spec is None:
        return None
    return _node(spec.get("id", id_), spec["icon"], x, y, w, h, spec["label"],
                 value=spec.get("value", ""), status=spec.get("status", ""), state=spec["state"],
                 frame=frame, hover=spec["hover"], rows=spec["rows"], soc=spec.get("soc"),
                 card=card, sub=spec.get("sub", ""))


def scene(g: dict, orientation: str = "landscape") -> dict:
    """Nodes and wires for one gateway, laid out for ``orientation``."""
    if orientation not in ("landscape", "portrait"):
        raise ValueError(f"orientation: 'landscape' or 'portrait', not {orientation!r}")
    grid, agate, home = _grid(g), _agate(g), _home(g)
    solars, bats, circs, gen = _solars(g), _batteries(g), _circuits(g), _generator(g)
    nodes: list[dict] = []
    wires: list[dict] = []
    land = orientation == "landscape"

    row = ([gen] if gen else []) + circs
    if land:
        A = _place(agate, "agate", 400, 250, 150, 150)
        G = _place(grid, "grid", 70, 275, 100, 100, frame=False)
        H = _place(home, "home", 425, 30, 100, 100, frame=False)
        S = [_place(s, s["id"], 640 + i * 120, 30, 100, 90, frame=False) for i, s in enumerate(solars)]
        B = [_place(b, b["id"], 660, 250 + i * 104, 280, 88, card=True) for i, b in enumerate(bats)]
        below = max([A["y"] + A["foot"]] + [b["y"] + b["h"] for b in B])
        C = [_place(c, c.get("id", "generator"), 240 + i * 120, below + 50, 90, 80) for i, c in enumerate(row)]
        width = 1000
    else:
        A = _place(agate, "agate", 145, 220, 130, 130)
        G = _place(grid, "grid", 20, 240, 90, 90, frame=False)
        H = _place(home, "home", 310, 240, 90, 90, frame=False)
        S = [_place(s, s["id"], 165 + (i - (len(solars) - 1) / 2) * 120, 20, 90, 80, frame=False)
             for i, s in enumerate(solars)]
        bus = A["y"] + A["foot"] + 12
        B = [_place(b, b["id"], 110, bus + 28 + i * 98, 280, 84, card=True) for i, b in enumerate(bats)]
        cy = (B[-1]["y"] + B[-1]["h"] + 46) if B else bus + 40
        C = [_place(c, c.get("id", "generator"), 30 + (i % 3) * 125, cy + (i // 3) * 150, 90, 80)
             for i, c in enumerate(row)]
        width = 420

    ax, ay, aw = A["x"], A["y"], A["w"]
    amid, abot = ay + A["h"] / 2, ay + A["foot"]
    nodes.append(A)
    if G:
        nodes.append(G)
        wires.append(_wire(G, A, grid["flow"], side_a="r", side_b="l"))
    if H:
        nodes.append(H)
        wires.append(_wire(A, H, home["flow"], side_a="t", side_b="b") if land
                     else _wire(A, H, home["flow"], side_a="r", side_b="l"))
    for k, (spec, n) in enumerate(zip(solars, S)):
        nodes.append(n)
        nx, nb = n["x"] + n["w"] / 2, n["y"] + n["foot"]
        if land:    # down, then left into the aGate's right side, above the battery cards
            ty = ay + 20 + k * 14
            d = f"M{nx:g} {nb:g} V{nb + 16 + k * 6:g} H{ax + aw + 40 + k * 8:g} V{ty:g} H{ax + aw:g}"
        else:       # straight down into the aGate's top
            d = f"M{nx:g} {nb:g} V{nb + 14:g} H{ax + aw / 2 + (k - (len(S) - 1) / 2) * 16:g} V{ay:g}"
        wires.append({"from": n["id"], "to": A["id"], "flow": spec["flow"], "dc": spec["dc"], "d": d})
    for spec, n in zip(bats, B):
        nodes.append(n)
        my = n["y"] + n["h"] / 2
        if land:
            d = f"M{ax + aw:g} {amid + 30:g} H{n['x'] - 30:g} V{my:g} H{n['x']:g}"
        else:       # a bus down the left edge, so no wire crosses a card
            d = f"M{ax + aw / 2:g} {abot:g} V{bus:g} H70 V{my:g} H{n['x']:g}"
        wires.append({"from": A["id"], "to": n["id"], "flow": spec["flow"], "dc": False, "d": d})
    for spec, n in zip(row, C):
        nodes.append(n)
        flow = spec["flow"] if spec is not gen else ("rev" if spec["flow"] == "fwd" else spec["flow"])
        nx, ny = n["x"] + n["w"] / 2, n["y"]
        if land:
            d = f"M{ax + aw / 2:g} {abot:g} V{ny - 22:g} H{nx:g} V{ny:g}"
        else:       # a bus down the right edge, clear of the battery cards
            d = f"M{ax + aw / 2:g} {abot:g} V{bus:g} H405 V{ny - 18:g} H{nx:g} V{ny:g}"
        wires.append({"from": A["id"], "to": n["id"], "flow": flow, "dc": False, "d": d})

    height = max(n["y"] + n["foot"] for n in nodes) + 24
    return {"orientation": orientation, "width": width, "height": height,
            "nodes": nodes, "wires": wires}
