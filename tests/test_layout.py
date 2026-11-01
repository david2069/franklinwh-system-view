"""The scene: what is drawn, where, and which way each wire flows."""
import pytest

from franklinwh_system_view import fixture, scene
from franklinwh_system_view.layout import MAX_UNITS

FIXTURES = ["us_backup_no_solar", "us_tou_two_apowers_solar", "us_outage", "offline",
            "six_apowers", "au_single_phase"]
ORIENTATIONS = ["landscape", "portrait"]


def gw(name):
    return fixture(name)["gateways"][0]


def ids(sc):
    return {n["id"] for n in sc["nodes"]}


def node(sc, id_):
    return next(n for n in sc["nodes"] if n["id"] == id_)


def wire(sc, a, b):
    return next(w for w in sc["wires"] if w["from"] == a and w["to"] == b)


def _overlap(a, b):
    """Pictures including the text under them."""
    return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]
                or a["y"] + a["foot"] <= b["y"] or b["y"] + b["foot"] <= a["y"])


@pytest.mark.parametrize("name", FIXTURES)
@pytest.mark.parametrize("orient", ORIENTATIONS)
def test_no_two_pictures_overlap_and_all_fit(name, orient):
    sc = scene(gw(name), orient)
    nodes = sc["nodes"]
    for i, a in enumerate(nodes):
        assert 0 <= a["x"] and a["x"] + a["w"] <= sc["width"], a["id"]
        assert a["y"] + a["foot"] <= sc["height"], a["id"]
        for b in nodes[i + 1:]:
            assert not _overlap(a, b), (a["id"], b["id"])


@pytest.mark.parametrize("orient", ORIENTATIONS)
def test_a_site_with_no_solar_draws_no_solar(orient):
    sc = scene(gw("us_backup_no_solar"), orient)
    assert not [n for n in sc["nodes"] if n["icon"] == "solar"]


def test_the_typical_us_site_is_aGate_one_battery_three_circuits():
    sc = scene(gw("us_backup_no_solar"))
    assert ids(sc) == {"agate", "grid", "home", "battery", "sc1", "sc2", "sc3"}
    assert node(sc, "agate")["status"] == "Emergency Backup"
    assert "kept ready for an outage" in node(sc, "agate")["hover"]
    assert node(sc, "sc3")["state"] == "off" and node(sc, "sc3")["icon"] == "toggleoff"


def test_flows_follow_the_signs():
    sc = scene(gw("us_tou_two_apowers_solar"))
    assert wire(sc, "solar", "agate")["flow"] == "fwd"        # solar into the aGate
    assert wire(sc, "agate", "battery")["flow"] == "fwd"      # charging: power_w < 0
    assert wire(sc, "agate", "home")["flow"] == "fwd"
    assert wire(sc, "grid", "agate")["flow"] == "idle"        # 0 W
    assert node(sc, "battery")["label"] == "Batteries ×2"
    au = scene(gw("au_single_phase"))
    assert wire(au, "grid", "agate")["flow"] == "rev"         # exporting: power_w < 0
    assert wire(au, "agate", "battery")["flow"] == "rev"      # discharging


def test_an_outage_is_red_and_its_wire_is_dead():
    sc = scene(gw("us_outage"))
    g = node(sc, "grid")
    assert (g["state"], g["status"], g["icon"]) == ("crit", "Outage", "gridout")
    assert wire(sc, "grid", "agate")["flow"] == "off"
    assert node(sc, "generator")["status"] == "Standby"


def test_an_offline_gateway_is_grey_and_says_so():
    sc = scene(gw("offline"))
    a = node(sc, "agate")
    assert (a["state"], a["status"]) == ("off", "Offline")
    assert node(sc, "grid")["state"] == "off"


def test_many_batteries_collapse_into_a_more_card_and_keep_their_states():
    sc = scene(gw("six_apowers"))
    cards = [n for n in sc["nodes"] if n["icon"] == "apower"]
    assert len(cards) == MAX_UNITS
    assert cards[-1]["label"] == "+3 more"          # 3 shown + 3 more = 6
    assert node(sc, "u3")["state"] == "warn" and node(sc, "u3")["status"] == "Warning"
    assert [n["id"] for n in sc["nodes"] if n["icon"] == "solar"] == ["pv1", "pv2"]


def test_portrait_is_phone_width():
    assert scene(gw("us_tou_two_apowers_solar"), "portrait")["width"] == 420


def test_an_unknown_orientation_is_refused():
    with pytest.raises(ValueError):
        scene(gw("offline"), "square")


def test_charge_is_a_whole_percent_everywhere():
    g = dict(gw("us_backup_no_solar"), battery={"soc_pct": 39.7, "power_w": 500})
    b = node(scene(g), "battery")
    assert b["soc"] == 40 and "40 % full" in b["hover"] and ["Charge", "40 %"] in b["rows"]


@pytest.mark.parametrize("name,node_id", [("grid", "grid"), ("home", "home"), ("solar", "solar"),
                                          ("battery", "battery"), ("circuits", "circuits"),
                                          ("generator", "generator")])
def test_what_a_bridge_cant_read_is_drawn_not_available_here(name, node_id):
    g = fixture("us_backup_no_solar")["gateways"][0]
    g["unavailable"] = [name]
    nodes = {n["id"]: n for n in scene(g)["nodes"]}
    assert nodes[node_id]["status"] == "Not available here" and nodes[node_id]["state"] == "off"
    if name == "circuits":
        assert not any(i.startswith("sc") for i in nodes)


def test_a_circuit_in_an_unknown_state_says_unknown_in_its_details():
    g = fixture("us_backup_no_solar")["gateways"][0]
    g["circuits"][0]["on"] = None
    sc1 = next(n for n in scene(g)["nodes"] if n["id"] == "sc1")
    assert sc1["status"] == "Unknown" and sc1["rows"] == [["State", "Unknown"]]
