"""Customise diagram: the form offered, the answers applied, and bad answers refused."""
import pytest

from franklinwh_system_view import build, customise, fixture, validate
from franklinwh_system_view.layout import scene, strip, weather_icon


def us():
    return fixture("us_backup_no_solar")


def by_key(fields, scope, key):
    return next(f for f in fields if f["scope"] == scope and f["key"] == key)


def test_empty_answers_change_nothing():
    assert customise.apply(us(), {}) == us()


def test_the_form_shows_the_reading_beside_each_answer():
    f = customise.fields(us(), {})
    assert by_key(f, "site", "name")["auto"] == "Los Angeles"
    assert by_key(f, "gw1", "legs")["help"] == "Your aGate reads 2 legs."
    assert by_key(f, "gw1", "solar")["help"] == "Your aGate reports no solar power."
    assert [x["key"] for x in f if x["key"].startswith("circuit")][:2] == ["circuit1_name", "circuit1_icon"]
    assert validate(dict(us(), customise={"endpoint": "x", "fields": f})) == []


def test_a_mismatch_with_a_reading_is_flagged_not_overridden():
    f = customise.fields(us(), {"gw1": {"legs": "L1"}})
    assert "aGate reads 2" in by_key(f, "gw1", "legs")["mismatch"]
    assert customise.apply(us(), {"gw1": {"legs": "L1"}})["gateways"][0]["legs"] == "L1"


def test_answers_draw_names_legs_models_and_appliances():
    p = customise.apply(us(), {"site": {"name": "Beach house"},
                               "gw1": {"name": "Garage aGate", "legs": "L1+L2", "battery_model": "aPower X",
                                       "circuit1_name": "Heat pump", "circuit1_icon": "hvac"}})
    g = p["gateways"][0]
    sc = {n["id"]: n for n in scene(g)["nodes"]}
    assert strip(p)["name"] == "Beach house"
    assert sc["agate"]["label"] == "Garage aGate"
    assert sc["grid"]["sub"] == "L1 + L2"
    assert sc["battery"]["label"] == "aPower X"
    assert (sc["sc1"]["label"], sc["sc1"]["icon"]) == ("Heat pump", "hvac")


def test_solar_and_generator_the_aGate_doesnt_report_are_drawn_as_not_reported():
    p = customise.apply(us(), {"gw1": {"solar": "apower", "generator": "fitted"}})
    sc = {n["id"]: n for n in scene(p["gateways"][0])["nodes"]}
    assert sc["solar"]["status"] == "Not reported" and sc["solar"]["state"] == "off"
    assert sc["generator"]["status"] == "Not reported"
    assert next(w for w in scene(p["gateways"][0])["wires"] if w["from"] == "solar")["dc"] is True


def test_no_solar_and_no_generator_hide_them():
    s = fixture("us_tou_two_apowers_solar")
    gid = s["gateways"][0]["id"]
    p = customise.apply(s, {gid: {"solar": "none", "generator": "none"}})
    assert p["gateways"][0]["solar"] == [] and p["gateways"][0]["generator"] is None


def test_a_catalogue_guess_prefills_the_model_marked_please_confirm():
    p = us()
    p["gateways"][0]["battery"]["model_guess"] = "aPower X"
    f = by_key(customise.fields(p, {}), "gw1", "battery_model")
    assert f["value"] == "aPower X" and f["confirm"] is True
    f = by_key(customise.fields(p, {"gw1": {"battery_model": "aPower 2"}}), "gw1", "battery_model")
    assert f["value"] == "aPower 2" and "confirm" not in f


def test_weather_can_be_hidden():
    assert strip(us())["weather"]["icon"] == "partcloud"
    assert "weather" not in strip(customise.apply(us(), {"site": {"weather": "hidden"}}))


def test_clean_keeps_known_answers_and_drops_automatic():
    assert customise.clean({"site": {"name": " Home ", "weather": ""}, "gw1": {"legs": "L1+L2"}}, us()) == \
        {"site": {"name": "Home"}, "gw1": {"legs": "L1+L2"}}


@pytest.mark.parametrize("bad", [[], {"nope": {}}, {"gw1": {"nope": "x"}}, {"gw1": {"legs": "L4"}},
                                 {"site": {"name": "x" * 61}}])
def test_clean_refuses_what_the_form_never_offers(bad):
    with pytest.raises(ValueError):
        customise.clean(bad, us())


@pytest.mark.parametrize("code,icon", [(0, "sun"), (2, "partcloud"), (3, "cloud"), (45, "fog"),
                                       (61, "rainlight"), (63, "rain"), (65, "rainheavy"),
                                       (73, "snow"), (95, "storm"), (None, None)])
def test_wmo_codes_map_to_a_picture(code, icon):
    assert weather_icon(code) == icon


def test_build_adds_the_strip():
    assert build(us())["strip"]["weather"]["text"] == "Partly cloudy · 18 °C"


def test_the_weather_sentence_keeps_the_unit():
    assert build(us())["strip"]["weather"]["hover"] == "Weather in Los Angeles now: partly cloudy, 18 °C. From Open-Meteo."
