"""Customise diagram: the user's answers where no reading tells a bridge how a site is built.

A bridge stores the answers as one JSON object (``saved``), keyed ``"site"`` or by gateway
id, and calls :func:`apply` on its payload before :func:`franklinwh_system_view.build`.
:func:`fields` describes the form the page shows. An empty answer means "Automatic": the
reading decides, or nothing is drawn. Where a reading exists it is shown beside the
answer, and a mismatch is flagged, never silently overridden.
"""
from __future__ import annotations

import copy
from typing import Any

LEG_CHOICES = [["", "Automatic"], ["L1", "L1"], ["L2", "L2"], ["L3", "L3"],
               ["L1+L2", "L1 + L2 (split-phase)"], ["L1+L2+L3", "L1 + L2 + L3 (three-phase)"]]
BATTERY_MODELS = [["", "Not set"], ["aPower X", "aPower X"], ["aPower 2", "aPower 2"],
                  ["aPower S", "aPower S"]]
SOLAR_CHOICES = [["", "Automatic (drawn when it reports power)"], ["agate", "On the aGate"],
                 ["apbox", "On an aPbox"], ["apower", "On an aPower S (DC)"],
                 ["ahub", "On an aHub port"], ["none", "No solar"]]
GENERATOR_CHOICES = [["", "Automatic (drawn when it runs)"], ["fitted", "Fitted"], ["none", "Not fitted"]]
CIRCUIT_ICONS = [["", "Switch"], ["hvac", "Heating / cooling"], ["water", "Hot water"],
                 ["ev", "EV charger"], ["pool", "Pool / spa"], ["other", "Other appliance"]]
WEATHER_CHOICES = [["", "Shown when a location is set"], ["hidden", "Hidden"]]


def _legs_reading(g: dict) -> str | None:
    """Only the number of legs is a reading; which legs they are is the user's answer."""
    n = len(((g.get("grid") or {}).get("legs_v")) or [])
    return {2: "L1+L2", 3: "L1+L2+L3"}.get(n)


def fields(payload: dict, saved: dict | None = None) -> list[dict]:
    """The Customise diagram form for ``payload`` (before :func:`apply`), filled from ``saved``."""
    saved = saved or {}
    site = payload.get("site") or {}
    s = saved.get("site") or {}
    out = [
        {"scope": "site", "group": "Site", "key": "name", "label": "Site name", "type": "text",
         "value": s.get("name", ""), "auto": site.get("name"),
         "help": "Empty uses the place from your location setting."},
        {"scope": "site", "group": "Site", "key": "weather", "label": "Weather", "type": "choice",
         "choices": WEATHER_CHOICES, "value": s.get("weather", "")},
    ]
    for g in payload.get("gateways") or []:
        gid, a = g["id"], saved.get(g["id"]) or {}
        group = a.get("name") or g.get("name") or gid
        f = lambda **kw: out.append({"scope": gid, "group": group, **kw})   # noqa: E731
        f(key="name", label="Name", type="text", value=a.get("name", ""), auto=g.get("name"))
        legs = _legs_reading(g)
        leg = {"key": "legs", "label": "Service legs", "type": "choice", "choices": LEG_CHOICES,
               "value": a.get("legs", "")}
        if legs:
            leg["help"] = f"Your aGate reads {legs.count('+') + 1} legs."
            if a.get("legs") and a["legs"].count("+") != legs.count("+"):
                leg["mismatch"] = (f"Your answer has {a['legs'].count('+') + 1} legs; "
                                   f"the aGate reads {legs.count('+') + 1}.")
        f(**leg)
        bat = g.get("battery") or {}
        guess = bat.get("model_guess")
        bm = {"key": "battery_model", "label": "Battery model", "type": "choice",
              "choices": BATTERY_MODELS, "value": a.get("battery_model", guess or "")}
        if guess and not a.get("battery_model"):
            bm["confirm"] = True
        f(**bm)
        reports = bool(g.get("solar"))
        f(key="solar", label="Solar", type="choice", choices=SOLAR_CHOICES, value=a.get("solar", ""),
          help="Your aGate reports solar power." if reports else "Your aGate reports no solar power.",
          **({"mismatch": "Your aGate reports solar power, but the answer says none."}
             if reports and a.get("solar") == "none" else {}))
        f(key="generator", label="Generator", type="choice", choices=GENERATOR_CHOICES,
          value=a.get("generator", ""))
        for c in g.get("circuits") or []:
            n = c.get("id")
            f(key=f"circuit{n}_name", label=f"Smart circuit {n} name", type="text",
              value=a.get(f"circuit{n}_name", ""), auto=c.get("name"))
            f(key=f"circuit{n}_icon", label=f"Smart circuit {n} picture", type="choice",
              choices=CIRCUIT_ICONS, value=a.get(f"circuit{n}_icon", ""))
    return out


def apply(payload: dict, saved: dict | None) -> dict:
    """``payload`` with the user's answers applied. ``payload`` itself is not changed."""
    out = copy.deepcopy(payload)
    saved = saved or {}
    s = saved.get("site") or {}
    site = out.setdefault("site", {})
    if s.get("name"):
        site["name"] = s["name"]
    if s.get("weather") == "hidden":
        site.pop("weather", None)
    for g in out.get("gateways") or []:
        a = saved.get(g["id"]) or {}
        if a.get("name"):
            g["name"] = a["name"]
        if a.get("legs"):
            g["legs"] = a["legs"]
        bat = g.get("battery")
        if bat is not None:
            model = a.get("battery_model") or bat.pop("model_guess", None)
            if model:
                bat["model"] = model
        sol = a.get("solar")
        if sol == "none":
            g["solar"] = []
        elif sol:
            arrays = g.get("solar") or [{"id": "solar", "power_w": None}]
            g["solar"] = [dict(x, where=sol) for x in arrays]
        gen = a.get("generator")
        if gen == "none":
            g["generator"] = None
        elif gen == "fitted" and not g.get("generator"):
            g["generator"] = {"power_w": None}
        for c in g.get("circuits") or []:
            n = c.get("id")
            if a.get(f"circuit{n}_name"):
                c["name"] = a[f"circuit{n}_name"]
            if a.get(f"circuit{n}_icon"):
                c["icon"] = a[f"circuit{n}_icon"]
    return out


def clean(values: Any, payload: dict) -> dict:
    """The answers a page sent, kept only where a field exists; raises ``ValueError`` otherwise.

    Empty answers are dropped, so "Automatic" is stored as no answer.
    """
    if not isinstance(values, dict):
        raise ValueError("expected an object keyed by 'site' or a gateway id")
    known: dict[str, dict] = {}
    for f in fields(payload):
        known.setdefault(f["scope"], {})[f["key"]] = f
    out: dict = {}
    for scope, answers in values.items():
        if scope not in known or not isinstance(answers, dict):
            raise ValueError(f"{scope!r}: not the site or a gateway")
        for key, v in answers.items():
            f = known[scope].get(key)
            if f is None:
                raise ValueError(f"{scope}.{key}: not a setting")
            v = "" if v is None else str(v).strip()
            if f["type"] == "choice" and v not in {c[0] for c in f["choices"]}:
                raise ValueError(f"{scope}.{key}: {v!r} is not one of the choices")
            if len(v) > 60:
                raise ValueError(f"{scope}.{key}: 60 characters at most")
            if v:
                out.setdefault(scope, {})[key] = v
    return out
