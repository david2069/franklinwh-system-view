"""Optional extras (owner, 2026-11-11): grid voltage and frequency, today's energy, the
power on each wire, and alarms. Each is switched on under Options; missing data is not drawn."""
import copy

from franklinwh_system_view import build, fixture, scene, validate


def _gw(**kw):
    g = copy.deepcopy(fixture("us_tou_two_apowers_solar")["gateways"][0])
    g.update(kw)
    return g


def _payload(g):
    return {"version": 1, "gateways": [g]}


ENERGY = {"grid_import_kwh": 3.2, "grid_export_kwh": 5.14, "solar_kwh": 21.4, "home_kwh": 12.0,
          "battery_charge_kwh": 8.1, "battery_discharge_kwh": 6.3}


def test_energy_and_alarms_validate():
    assert validate(_payload(_gw(energy_today=ENERGY,
                                 alarms=[{"target": "agate", "text": "Grid voltage high", "level": "warn"},
                                         {"target": "battery", "unit": 1, "code": 3021, "text": "Cell over-temp", "level": "crit"}]))) == []
    bad = validate(_payload(_gw(energy_today={"solar_kwh": "lots"},
                                alarms=[{"target": "roof", "text": "", "level": "loud"}])))
    assert any("energy_today.solar_kwh" in e for e in bad)
    assert any("alarms[0].target" in e for e in bad)
    assert any("alarms[0].text" in e for e in bad)
    assert any("alarms[0].level" in e for e in bad)


def test_old_payloads_still_build():
    out = build(fixture("us_backup_no_solar"))
    for n in out["gateways"][0]["scenes"]["landscape"]["nodes"]:
        assert n.get("extra", []) == [] or all(x["k"] == "vhz" for x in n["extra"])
        assert n.get("alarms", []) == []


def _node(sc, id_):
    return next(n for n in sc["nodes"] if n["id"] == id_)


def test_grid_shows_voltage_and_frequency_as_an_extra():
    sc = scene(_gw(), "landscape")
    assert {"k": "vhz", "t": "240.2 V · 60.00 Hz"} in _node(sc, "grid")["extra"]


def test_energy_today_on_each_node():
    for o in ("landscape", "portrait"):
        sc = scene(_gw(energy_today=ENERGY), o)
        assert [x["t"] for x in _node(sc, "grid")["extra"] if x["k"] == "energy"] == [
            "Today in 3.2 kWh", "out 5.1 kWh"]
        assert {"k": "energy", "t": "Today 21.4 kWh"} in _node(sc, "solar")["extra"]
        assert {"k": "energy", "t": "Today 12.0 kWh"} in _node(sc, "home")["extra"]
        assert {"k": "energy", "t": "Today in 8.1 · out 6.3 kWh"} in _node(sc, "battery")["extra"]


def test_a_missing_energy_value_is_left_out():
    sc = scene(_gw(energy_today={"home_kwh": None, "solar_kwh": 2.0}), "landscape")
    assert not any(x["k"] == "energy" for x in _node(sc, "home").get("extra", []))
    assert not any(x["k"] == "energy" for x in _node(sc, "grid").get("extra", []))


def test_wires_carry_their_power_and_direction():
    sc = scene(_gw(), "landscape")
    by_to = {(w["from"], w["to"]): w for w in sc["wires"]}
    bat = by_to[("agate", "battery")]
    assert bat["kw"] == "2.90 kW" and bat["flow"] == "fwd"     # charging: aGate → battery
    assert len(bat["mid"]) == 2 and bat["ang"] == 0             # rightwards, towards the card
    grid = by_to[("grid", "agate")]
    assert "kw" not in grid                                       # 0 W: idle, nothing to label
    home = by_to[("agate", "home")]
    assert home["kw"] == "1.30 kW" and home["ang"] == 270        # up, into the home (landscape)


def test_alarms_attach_to_their_object():
    alarms = [{"target": "agate", "text": "Grid voltage high", "level": "warn"},
              {"target": "battery", "text": "Cell over-temp", "level": "crit", "code": 3021}]
    sc = scene(_gw(alarms=alarms), "landscape")
    assert _node(sc, "agate")["alarms"] == [{"text": "Grid voltage high", "level": "warn"}]
    assert _node(sc, "battery")["alarms"] == [{"text": "Cell over-temp", "level": "crit", "code": 3021}]


def test_a_unit_alarm_goes_to_that_units_card():
    g = _gw(battery={"units": [{"id": "a1", "name": "aPower 1", "soc_pct": 50, "power_w": 0},
                               {"id": "a2", "name": "aPower 2", "soc_pct": 51, "power_w": 0}]},
            alarms=[{"target": "battery", "unit": 2, "text": "Fan fault", "level": "warn"}])
    sc = scene(g, "landscape")
    assert _node(sc, "a2")["alarms"] == [{"text": "Fan fault", "level": "warn"}]
    assert not _node(sc, "a1").get("alarms")
