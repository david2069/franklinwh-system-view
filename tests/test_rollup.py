"""Battery roll-up (#11, owner 2026-11-17): with several aPowers, one battery picture shows
the gateway's totals as the aGate reports them and the count; the hover and the details
list each aPower. ``battery.rollup`` asks for it; without it the per-unit cards stay."""
import pathlib

import pytest

from franklinwh_system_view import build, fixture, scene

JS = (pathlib.Path(__file__).resolve().parents[1] / "src/franklinwh_system_view/static/system-view.js").read_text()

UNITS = [{"id": "ap1", "name": "aP1", "soc_pct": 63.6, "soh_pct": 95.0, "current_a": 4.5, "state": "ok",
          "status": "Discharging"},
         {"id": "ap2", "name": "aP2", "soc_pct": 59.6, "soh_pct": 93.5, "current_a": 4.6, "status": "Discharging"},
         {"id": "ap3", "name": "aP3", "soc_pct": 55.6, "soh_pct": 92.0, "current_a": 4.6, "status": "Discharging"},
         {"id": "ap4", "name": "aP4", "soc_pct": 51.6, "soh_pct": 90.5, "current_a": 4.6, "status": "Discharging",
          "state": "warn"}]


def gw(**bat):
    g = dict(fixture("us_backup_no_solar")["gateways"][0])
    g["battery"] = dict({"soc_pct": 64, "power_w": 200, "count": 4, "rollup": True, "units": UNITS}, **bat)
    return g


def bats(sc):
    return [n for n in sc["nodes"] if n["icon"] == "apower"]


def test_one_picture_with_the_count_and_the_gateways_totals():
    cards = bats(scene(gw()))
    assert len(cards) == 1
    b = cards[0]
    assert b["id"] == "battery" and b["label"] == "Batteries ×4"
    assert b["soc"] == 64 and b["value"] == "0.20 kW" and b["status"] == "Discharging"


def test_the_hover_has_a_line_per_apower():
    h = bats(scene(gw()))[0]["hover"]
    lines = h.split("\n")
    assert lines[0].startswith("Batteries ×4 is 64 % full")
    assert lines[1:] == ["aP1 64 % · 4.5 A · Discharging", "aP2 60 % · 4.6 A · Discharging",
                         "aP3 56 % · 4.6 A · Discharging", "aP4 52 % · 4.6 A · Discharging"]


def test_the_details_have_a_row_per_apower():
    rows = dict(bats(scene(gw()))[0]["rows"])
    assert rows["aP1"] == "64 % · SoH 95 % · 4.5 A · Discharging"
    assert rows["aP4"] == "52 % · SoH 90.5 % · 4.6 A · Discharging"
    assert rows["Charge"] == "64 %"


def test_a_unit_warning_shows_on_the_one_picture():
    assert bats(scene(gw()))[0]["state"] == "warn"


def test_a_unit_alarm_goes_to_the_one_picture():
    g = gw()
    g["alarms"] = [{"target": "battery", "unit": 3, "text": "aP3 over temperature", "level": "warn"}]
    assert bats(scene(g))[0]["alarms"] == [{"text": "aP3 over temperature", "level": "warn"}]


def test_what_a_unit_doesnt_report_is_left_out():
    g = gw(units=[{"name": "aP1", "soc_pct": 50}, {"name": "aP2"}], count=2)
    b = bats(scene(g))[0]
    assert dict(b["rows"])["aP1"] == "50 %" and dict(b["rows"])["aP2"] == "–"


def test_the_count_comes_from_the_units_when_not_given():
    assert bats(scene(gw(count=None)))[0]["label"] == "Batteries ×4"


def test_without_rollup_the_per_unit_cards_stay():
    sc = scene(fixture("six_apowers")["gateways"][0])
    assert len(bats(sc)) == 4 and bats(sc)[-1]["label"] == "+3 more"


def test_build_validates_a_rollup_payload():
    out = build({"version": 1, "site": {"name": "x"}, "gateways": [gw()]})
    land = out["gateways"][0]["scenes"]["landscape"]
    assert [n["label"] for n in land["nodes"] if n["icon"] == "apower"] == ["Batteries ×4"]
    with pytest.raises(ValueError, match="rollup"):
        build({"version": 1, "site": {"name": "x"}, "gateways": [gw(rollup="yes")]})


@pytest.mark.parametrize("orient", ["landscape", "portrait"])
def test_the_rollup_fixture_lays_out(orient):
    sc = scene(fixture("four_apowers_rollup")["gateways"][0], orient)
    assert [n["label"] for n in bats(sc)] == ["Batteries ×4"]


def test_the_page_draws_hover_and_details_line_by_line():
    assert JS.count('.replace(/\\n/g, "<br>")') >= 2
