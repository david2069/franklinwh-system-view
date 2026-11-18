"""Solar forecast & actual (owner, Direct Connect Bridge, 2026-11-19): today's forecast, what
the panels made so far and what is still to come, from the bridge's own forecast. Shown on the
left of the diagram when switched on under Options; a bridge without a forecast sends none."""
import copy

from franklinwh_system_view import build, fixture, validate
from franklinwh_system_view.layout import solar_today


def _gw(**kw):
    g = copy.deepcopy(fixture("us_tou_two_apowers_solar")["gateways"][0])
    g.pop("solar_forecast", None)
    g.update(kw)
    return g


SF = {"forecast_kwh": 21.4, "actual_kwh": 12.3, "remaining_kwh": 9.1}


def test_solar_forecast_validates():
    assert validate({"version": 1, "gateways": [_gw(solar_forecast=SF)]}) == []
    bad = validate({"version": 1, "gateways": [_gw(solar_forecast={"forecast_kwh": "sunny", "cloudy": 1})]})
    assert any("solar_forecast.forecast_kwh" in e for e in bad)
    assert any("solar_forecast.cloudy" in e for e in bad)
    assert any("solar_forecast" in e for e in validate({"version": 1, "gateways": [_gw(solar_forecast=[1])]}))


def test_rows_for_what_was_sent_and_nothing_without_a_forecast():
    t = solar_today(_gw(solar_forecast=SF))
    assert t["title"] == "Solar today"
    assert t["rows"] == [["Forecast", "21.4 kWh"], ["Actual so far", "12.3 kWh"],
                         ["Still to come", "9.1 kWh"]]
    assert t["pct"] == 57                     # actual against the forecast
    assert solar_today(_gw(solar_forecast={"forecast_kwh": 21.4})) == {
        "title": "Solar today", "rows": [["Forecast", "21.4 kWh"]], "pct": None}
    assert solar_today(_gw()) is None
    assert solar_today(_gw(solar_forecast={"forecast_kwh": None, "actual_kwh": None})) is None


def test_build_sends_it_with_each_gateway():
    out = build({"version": 1, "gateways": [_gw(solar_forecast=SF), _gw(id="gw9", name="Shed")]})
    assert out["gateways"][0]["solar_today"]["rows"][0] == ["Forecast", "21.4 kWh"]
    assert out["gateways"][1]["solar_today"] is None
