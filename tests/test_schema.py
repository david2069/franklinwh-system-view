"""The payload contract and the package's own entry points."""
import pytest

from franklinwh_system_view import build, fixture, static_dir, validate

FIXTURES = ["us_backup_no_solar", "us_tou_two_apowers_solar", "us_outage", "offline",
            "six_apowers", "au_single_phase"]


@pytest.mark.parametrize("name", FIXTURES)
def test_every_shipped_example_is_valid(name):
    assert validate(fixture(name)) == []


def test_every_problem_is_reported_with_its_path():
    bad = {"version": 1, "gateways": [
        {"id": "a", "name": "A", "online": "yes", "grid": {"state": "down"},
         "battery": {"soc_pct": 140}, "solar": [{"where": "roof"}], "unavailable": ["pool"]},
        {"id": "a", "name": "", "online": True}]}
    errs = validate(bad)
    for want in ("gateways: ids must be unique", "gateways[0].online", "gateways[0].grid.state",
                 "gateways[0].battery.soc_pct", "gateways[0].solar[0].where",
                 "gateways[0].unavailable", "gateways[1].name"):
        assert any(e.startswith(want) for e in errs), want


def test_the_wrong_version_is_refused():
    assert validate({"version": 2, "gateways": []}) == ["version: must be 1"]


def test_build_adds_both_scenes_and_refuses_bad_payloads():
    out = build(fixture("us_backup_no_solar"))
    assert set(out["gateways"][0]["scenes"]) == {"landscape", "portrait"}
    with pytest.raises(ValueError, match="online"):
        build({"version": 1, "gateways": [{"id": "a", "name": "A"}]})


def test_the_page_files_ship_with_the_package():
    d = static_dir()
    assert (d / "system-view.js").is_file() and (d / "system-view.css").is_file()
