"""The FranklinWH System view: one picture of a site's hardware, shared by both bridges.

A bridge builds a payload (``schema``), the layout turns each gateway into a scene, and the
page in ``static/`` draws it as an overlay over the bridge's own UI.
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from . import customise
from .layout import _circuits, scene, site_groups, site_scene, solar_today, strip
from .schema import SCHEMA_VERSION, validate

__version__ = "0.5.1"
__all__ = ["SCHEMA_VERSION", "build", "customise", "fixture", "scene", "static_dir", "validate"]


def static_dir() -> Path:
    """The folder a bridge serves at ``/system-view/`` (system-view.js and .css)."""
    return Path(str(resources.files(__package__) / "static"))


def build(payload: dict) -> dict:
    """``payload`` plus both scenes for every gateway, ready to send to the page; and, for
    each site that two or more gateways name, ``site_groups`` with its own scenes.

    Raises ``ValueError`` listing every problem when the payload is invalid.
    """
    errs = validate(payload)
    if errs:
        raise ValueError("; ".join(errs))
    out = dict(payload)
    out["strip"] = strip(payload)
    out["gateways"] = [dict(g, scenes=_scenes(g), solar_today=solar_today(g)) for g in payload["gateways"]]
    groups = site_groups(payload)
    if groups:      # a site with two or more gateways: one diagram for all of them
        by = {g["id"]: g for g in payload["gateways"]}
        out["site_groups"] = [dict(s, scenes=_site_scenes([by[i] for i in s["gateway_ids"]]))
                              for s in groups]
    return out


def _scenes(g: dict) -> dict:
    """Both orientations, and each without the smart circuits when there are any (the user
    can hide them under Options), laid out again so no gap is left."""
    out = {}
    for o in ("landscape", "portrait"):
        out[o] = scene(g, o)
        if _circuits(g):
            out[o + "_no_circuits"] = scene(g, o, circuits=False)
    return out


def _site_scenes(members: list[dict]) -> dict:
    """The site diagram in both orientations, and each without the smart circuits when any
    of its gateways has them."""
    out = {}
    for o in ("landscape", "portrait"):
        out[o] = site_scene(members, o)
        if any(_circuits(g) for g in members):
            out[o + "_no_circuits"] = site_scene(members, o, circuits=False)
    return out


def fixture(name: str) -> dict:
    """An example payload shipped with the package (see ``fixtures/``), for tests and demos."""
    import json
    return json.loads((resources.files(__package__) / "fixtures" / f"{name}.json").read_text())
