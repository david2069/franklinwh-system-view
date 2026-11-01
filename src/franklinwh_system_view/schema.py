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
    for i, c in enumerate(g.get("circuits") or []):
        if not isinstance(c.get("on"), (bool, type(None))):
            errs.append(f"{path}.circuits[{i}].on: true, false or null")
    for name in g.get("unavailable") or []:
        if name not in OBJECTS:
            errs.append(f"{path}.unavailable: {name!r} is not one of {OBJECTS}")
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
    return errs
