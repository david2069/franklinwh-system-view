"""A site with several gateways (Direct Connect Bridge #662): one diagram for all of them.

The grid and the service meter on the left, then one row per aGate with its batteries, its
solar or smart circuits, and its home; what the payload leaves out is not drawn.
"""
import copy

import pytest

from franklinwh_system_view import build, fixture, validate
from franklinwh_system_view.layout import site_groups, site_scene

ORIENTATIONS = ["landscape", "portrait"]


def site():
    return fixture("three_gateway_site")


def members(p, sid="home"):
    return [g for g in p["gateways"] if (g.get("site") or {}).get("id") == sid]


def node(sc, id_):
    return next(n for n in sc["nodes"] if n["id"] == id_)


def _overlap(a, b):
    return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]
                or a["y"] + a["foot"] <= b["y"] or b["y"] + b["foot"] <= a["y"])


def test_the_site_field_is_optional_and_checked():
    assert validate(site()) == []
    assert validate(fixture("two_gateways")) == []          # old payloads stay valid
    bad = site()
    bad["gateways"][0]["site"] = {"id": "", "name": 3}
    bad["gateways"][1]["site"]["meter"] = {"id": "m1", "ac": "four", "rated_amps": "63"}
    bad["gateways"][2]["site"] = "home"
    errs = validate(bad)
    for want in ("gateways[0].site.id", "gateways[0].site.name", "gateways[1].site.meter.ac",
                 "gateways[1].site.meter.rated_amps", "gateways[2].site"):
        assert any(e.startswith(want) for e in errs), want


def test_only_a_site_with_two_or_more_gateways_is_grouped():
    assert site_groups(site()) == [{"id": "home", "name": "Home", "gateway_ids": ["gw1", "gw2", "gw3"]}]
    out = build(site())
    assert [s["id"] for s in out["site_groups"]] == ["home"]
    assert set(out["site_groups"][0]["scenes"]) == {"landscape", "portrait",
                                                  "landscape_no_circuits", "portrait_no_circuits"}
    # A payload without sites, or with one gateway per site, is built as before.
    assert "site_groups" not in build(fixture("two_gateways"))
    one = site()
    one["gateways"] = one["gateways"][2:]
    assert "site_groups" not in build(one)


@pytest.mark.parametrize("orient", ORIENTATIONS)
def test_one_row_per_aGate_fed_from_the_meter(orient):
    sc = site_scene(members(site()), orient)
    agates = [n for n in sc["nodes"] if n.get("pick")]
    assert [n["pick"] for n in agates] == ["gw1", "gw2", "gw3"]
    assert [n["y"] for n in agates] == sorted(n["y"] for n in agates)      # top to bottom
    assert [n["label"] for n in agates] == ["aGate 1 · L1", "aGate 2 · L2", "aGate 3 · L3"]
    grid, meter = node(sc, "grid"), node(sc, "meter")
    assert max(grid["x"] + grid["w"], meter["x"] + meter["w"]) < min(n["x"] for n in agates)  # on the left
    if orient == "landscape":
        assert grid["x"] < meter["x"]                                       # grid, then meter
    else:
        assert grid["y"] < meter["y"]                                       # a phone: one above the other
    assert meter["status"] == "3 × 63 A" and meter["sub"] == "Meter 1"
    feeds = [w for w in sc["wires"] if w["from"] == "meter"]
    assert [(w["to"], w["gw"]) for w in feeds] == [("gw1/agate", "gw1"), ("gw2/agate", "gw2"),
                                                   ("gw3/agate", "gw3")]
    assert [w["flow"] for w in feeds] == ["rev", "fwd", "idle"]           # export, import, none
    assert next(w for w in sc["wires"] if w["from"] == "grid")["to"] == "meter"


@pytest.mark.parametrize("orient", ORIENTATIONS)
@pytest.mark.parametrize("circuits", [True, False])
def test_no_two_pictures_overlap_and_all_fit(orient, circuits):
    sc = site_scene(members(site()), orient, circuits=circuits)
    nodes = sc["nodes"]
    assert len({n["id"] for n in nodes}) == len(nodes)
    for i, a in enumerate(nodes):
        assert 0 <= a["x"] and a["x"] + a["w"] <= sc["width"], a["id"]
        assert a["y"] + a["foot"] <= sc["height"], a["id"]
        for b in nodes[i + 1:]:
            assert not _overlap(a, b), (a["id"], b["id"])
    if orient == "portrait":
        assert sc["width"] == 420


def test_each_row_draws_only_what_its_gateway_reports():
    sc = site_scene(members(site()))
    row = lambda gid: {n["id"].split("/", 1)[1] for n in sc["nodes"] if n.get("gw") == gid}  # noqa: E731
    assert row("gw1") == {"agate", "battery", "solar", "home"}             # solar, no circuits
    assert row("gw2") == {"agate", "battery", "sc1", "sc2", "home"}        # circuits, no solar
    assert node(sc, "gw2/sc1")["icon"] == "hvac"
    no_c = site_scene(members(site()), circuits=False)
    assert not [n for n in no_c["nodes"] if "/sc" in n["id"]]


def test_the_site_grid_is_the_sum_and_unknown_when_one_is_unknown():
    sc = site_scene(members(site()))
    g = node(sc, "grid")
    assert g["value"] == "1.30 kW" and g["status"] == "Connected"           # -1.2 + 2.5 + 0
    assert ["aGate 1", "Exporting 1.20 kW"] in g["rows"]
    p = site()
    p["gateways"][2]["grid"]["power_w"] = None
    assert node(site_scene(members(p)), "grid")["value"] == "–"


def test_an_outage_on_every_aGate_is_red_and_on_one_is_amber():
    p = site()
    for g in members(p):
        g["grid"] = {"state": "outage", "power_w": 0}
    g = node(site_scene(members(p)), "grid")
    assert (g["state"], g["status"], g["icon"]) == ("crit", "Outage", "gridout")
    p = site()
    p["gateways"][1]["grid"] = {"state": "outage", "power_w": 0}
    sc = site_scene(members(p))
    g = node(sc, "grid")
    assert (g["state"], g["status"]) == ("warn", "Outage at aGate 2")
    assert next(w for w in sc["wires"] if w["to"] == "gw2/agate")["flow"] == "off"


def test_no_service_meter_is_drawn_unless_every_aGate_names_the_same_one():
    p = site()
    p["gateways"][1]["site"]["meter"] = {"id": "m2"}
    sc = site_scene(members(p))
    assert not [n for n in sc["nodes"] if n["id"] == "meter"]
    assert [w["to"] for w in sc["wires"] if w["from"] == "grid"] == ["gw1/agate", "gw2/agate", "gw3/agate"]
    for g in members(p):
        del g["site"]["meter"]
    assert not [n for n in site_scene(members(p))["nodes"] if n["id"] == "meter"]


def test_a_meter_with_no_rating_says_nothing_about_it():
    p = site()
    for g in members(p):
        g["site"]["meter"] = {"id": "m1"}
    m = node(site_scene(members(p)), "meter")
    assert (m["label"], m["status"]) == ("Service meter", "")


def test_a_rows_extras_and_alarms_stay_on_its_own_pictures():
    p = site()
    p["gateways"][0]["energy_today"] = {"home_kwh": 9.5}
    p["gateways"][1]["alarms"] = [{"target": "grid", "text": "Voltage high", "level": "warn"},
                                  {"target": "agate", "text": "Fan", "level": "crit"}]
    sc = site_scene(members(p))
    assert node(sc, "gw1/home")["extra"] == [{"k": "energy", "t": "Today 9.5 kWh"}]
    assert node(sc, "gw2/agate")["alarms"] == [{"text": "Fan", "level": "crit"}]
    assert node(sc, "grid")["alarms"] == [{"text": "aGate 2: Voltage high", "level": "warn"}]


def test_the_input_payload_is_not_changed():
    p = site()
    before = copy.deepcopy(p)
    build(p)
    assert p == before
