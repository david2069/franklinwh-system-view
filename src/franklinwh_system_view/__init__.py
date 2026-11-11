"""The FranklinWH System view: one picture of a site's hardware, shared by both bridges.

A bridge builds a payload (``schema``), the layout turns each gateway into a scene, and the
page in ``static/`` draws it as an overlay over the bridge's own UI.
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from . import customise
from .layout import scene, strip
from .schema import SCHEMA_VERSION, validate

__version__ = "0.3.1"
__all__ = ["SCHEMA_VERSION", "build", "customise", "fixture", "scene", "static_dir", "validate"]


def static_dir() -> Path:
    """The folder a bridge serves at ``/system-view/`` (system-view.js and .css)."""
    return Path(str(resources.files(__package__) / "static"))


def build(payload: dict) -> dict:
    """``payload`` plus both scenes for every gateway, ready to send to the page.

    Raises ``ValueError`` listing every problem when the payload is invalid.
    """
    errs = validate(payload)
    if errs:
        raise ValueError("; ".join(errs))
    out = dict(payload)
    out["strip"] = strip(payload)
    out["gateways"] = [dict(g, scenes={o: scene(g, o) for o in ("landscape", "portrait")})
                       for g in payload["gateways"]]
    return out


def fixture(name: str) -> dict:
    """An example payload shipped with the package (see ``fixtures/``), for tests and demos."""
    import json
    return json.loads((resources.files(__package__) / "fixtures" / f"{name}.json").read_text())
