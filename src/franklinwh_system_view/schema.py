"""The payload a bridge hands the System view: one site, its gateways and what each reads.

Both bridges build this from their own data. Anything a bridge can't read is left out
(``None`` or an empty list) or named in ``unavailable``; nothing is guessed here.

Signs: ``grid.power_w`` > 0 imports from the grid; ``battery.power_w`` > 0 discharges.
"""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = 1

GRID_STATES = ("connected", "outage", "spike", "unknown")
DEVICE_STATES = ("ok", "warn", "crit", "off")
SOLAR_WHERE = ("agate", "apbox", "apower", "ahub", "panel")
KINDS = ("agate", "mac")
OBJECTS = ("grid", "agate", "home", "solar", "battery", "circuits", "generator")
LEGS = ("L1", "L2", "L3", "L1+L2", "L1+L2+L3")
CIRCUIT_ICONS = ("circuit", "hvac", "water", "ev", "pool", "other")
FIELD_TYPES = ("text", "choice")
ENERGY_KEYS = ("grid_import_kwh", "grid_export_kwh", "solar_kwh", "home_kwh",
               "battery_charge_kwh", "battery_discharge_kwh")
ALARM_LEVELS = ("warn", "crit")


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_gateway(g: Any, path: str) -> list[str]:
    errs: list[str] = []
    if not isinstance(g, dict):
        return [f"{path}: not an object"]
    for key in ("id", "name"):
        if not isinstance(g.get(key), str) or not g.get(key):
            errs.append(f"{path}.{key}: a non-empty string is required")
    if g.get("kind", "agate") not in KINDS:
        errs.append(f"{path}.kind: one of {KINDS}")
    if not isinstance(g.get("online"), bool):
        errs.append(f"{path}.online: true or false is required")
    grid = g.get("grid")
    if grid is not None:
        if grid.get("state") not in GRID_STATES:
            errs.append(f"{path}.grid.state: one of {GRID_STATES}")
        for k in ("power_w", "voltage_v", "freq_hz"):
            if grid.get(k) is not None and not _num(grid[k]):
                errs.append(f"{path}.grid.{k}: a number or null")
    bat = g.get("battery")
    if bat is not None:
        if bat.get("soc_pct") is not None and not (_num(bat["soc_pct"]) and 0 <= bat["soc_pct"] <= 100):
            errs.append(f"{path}.battery.soc_pct: 0–100 or null")
        for i, u in enumerate(bat.get("units") or []):
            if u.get("state", "ok") not in DEVICE_STATES:
                errs.append(f"{path}.battery.units[{i}].state: one of {DEVICE_STATES}")
    for i, s in enumerate(g.get("solar") or []):
        if s.get("where") not in SOLAR_WHERE:
            errs.append(f"{path}.solar[{i}].where: one of {SOLAR_WHERE}")
        if s.get("power_w") is not None and not _num(s["power_w"]):
            errs.append(f"{path}.solar[{i}].power_w: a number or null")
    if g.get("legs") is not None and g["legs"] not in LEGS:
        errs.append(f"{path}.legs: one of {LEGS}")
    for i, c in enumerate(g.get("circuits") or []):
        if not isinstance(c.get("on"), (bool, type(None))):
            errs.append(f"{path}.circuits[{i}].on: true, false or null")
        if c.get("icon", "circuit") not in CIRCUIT_ICONS:
            errs.append(f"{path}.circuits[{i}].icon: one of {CIRCUIT_ICONS}")
    en = g.get("energy_today")
    if en is not None:
        if not isinstance(en, dict):
            errs.append(f"{path}.energy_today: an object or null")
        else:
            for k, v in en.items():
                if k not in ENERGY_KEYS:
                    errs.append(f"{path}.energy_today.{k}: not one of {ENERGY_KEYS}")
                elif v is not None and not _num(v):
                    errs.append(f"{path}.energy_today.{k}: a number or null")
    al = g.get("alarms")
    if al is not None and not isinstance(al, list):
        errs.append(f"{path}.alarms: a list or null")
    for i, a in enumerate(al if isinstance(al, list) else []):
        p = f"{path}.alarms[{i}]"
        if not isinstance(a, dict):
            errs.append(f"{p}: not an object")
            continue
        if a.get("target") not in OBJECTS:
            errs.append(f"{p}.target: one of {OBJECTS}")
        if not isinstance(a.get("text"), str) or not a.get("text"):
            errs.append(f"{p}.text: a non-empty string is required")
        if a.get("level") not in ALARM_LEVELS:
            errs.append(f"{p}.level: one of {ALARM_LEVELS}")
        if a.get("unit") is not None and (not isinstance(a["unit"], int) or isinstance(a["unit"], bool)):
            errs.append(f"{p}.unit: an integer or null")
    for name in g.get("unavailable") or []:
        if name not in OBJECTS:
            errs.append(f"{path}.unavailable: {name!r} is not one of {OBJECTS}")
    return errs


def _check_site(s: Any) -> list[str]:
    if s is None:
        return []
    if not isinstance(s, dict):
        return ["site: not an object"]
    errs: list[str] = []
    w = s.get("weather")
    if w is not None:
        if not isinstance(w, dict):
            errs.append("site.weather: an object or null")
        else:
            if w.get("code") is not None and not isinstance(w["code"], int):
                errs.append("site.weather.code: a WMO weather code (integer) or null")
            if w.get("temp_c") is not None and not _num(w["temp_c"]):
                errs.append("site.weather.temp_c: a number or null")
    return errs


def _check_customise(c: Any) -> list[str]:
    """The Customise diagram form: where to save, and the fields the bridge offers."""
    if c is None:
        return []
    if not isinstance(c, dict) or not isinstance(c.get("endpoint"), str):
        return ["customise.endpoint: a URL string is required"]
    errs: list[str] = []
    for i, f in enumerate(c.get("fields") or []):
        p = f"customise.fields[{i}]"
        if not isinstance(f, dict):
            errs.append(f"{p}: not an object")
            continue
        for key in ("scope", "key", "label"):
            if not isinstance(f.get(key), str) or not f.get(key):
                errs.append(f"{p}.{key}: a non-empty string is required")
        if f.get("type") not in FIELD_TYPES:
            errs.append(f"{p}.type: one of {FIELD_TYPES}")
        elif f["type"] == "choice":
            ch = f.get("choices")
            if not isinstance(ch, list) or not all(isinstance(x, list) and len(x) == 2 for x in ch):
                errs.append(f"{p}.choices: a list of [value, label] pairs")
    return errs


def validate(payload: Any) -> list[str]:
    """Every problem with ``payload``, each with its path; ``[]`` when it is valid."""
    if not isinstance(payload, dict):
        return ["payload: not an object"]
    errs: list[str] = []
    if payload.get("version") != SCHEMA_VERSION:
        errs.append(f"version: must be {SCHEMA_VERSION}")
    gws = payload.get("gateways")
    if not isinstance(gws, list):
        return errs + ["gateways: a list is required"]
    ids = [g.get("id") for g in gws if isinstance(g, dict)]
    if len(ids) != len(set(ids)):
        errs.append("gateways: ids must be unique")
    for i, g in enumerate(gws):
        errs += _check_gateway(g, f"gateways[{i}]")
    return errs + _check_site(payload.get("site")) + _check_customise(payload.get("customise"))
