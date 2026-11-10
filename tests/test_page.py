"""The overlay in a real browser: opens, draws, zooms, shows details, closes, remembers.

Needs Playwright with a Chrome or Chromium; skipped where it isn't installed.
"""
import threading

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

from franklinwh_system_view.demo import serve  # noqa: E402


@pytest.fixture(scope="module")
def base():
    srv = serve(port=0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome", headless=True)
        except Exception:  # noqa: BLE001
            try:
                b = p.chromium.launch(headless=True)
            except Exception as e:  # noqa: BLE001
                pytest.skip(f"no browser: {e}")
        yield b
        b.close()


def _page(browser, base, query="", width=1280, height=800):
    ctx = browser.new_context(viewport={"width": width, "height": height})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.goto(base + "/" + query)
    return ctx, page, errors


def test_opens_over_the_dashboard_and_closes_back_to_it(browser, base):
    ctx, page, errors = _page(browser, base)
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj[data-id='agate']")
    assert page.url.endswith("#system")
    assert page.locator(".fwhsv-obj").count() == 7          # grid, aGate, home, battery, 3 circuits
    assert page.locator(".fwhsv-obj[data-id^='solar']").count() == 0
    page.click(".fwhsv-close")
    assert page.locator(".fwhsv").is_hidden()
    assert not page.url.endswith("#system")
    assert errors == []
    ctx.close()


def test_click_shows_details_and_hover_shows_a_sentence(browser, base):
    ctx, page, errors = _page(browser, base, "?fixture=us_tou_two_apowers_solar")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj[data-id='battery']")
    page.hover(".fwhsv-obj[data-id='solar']")
    assert "producing" in page.locator(".fwhsv-tip").inner_text()
    page.click(".fwhsv-obj[data-id='battery']")
    assert "Batteries ×2" in page.locator(".fwhsv-panel").inner_text()
    assert "Charging" in page.locator(".fwhsv-panel").inner_text()
    assert errors == []
    ctx.close()


def test_zoom_buttons_change_the_view_and_fit_restores_it(browser, base):
    ctx, page, _ = _page(browser, base)
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    vb0 = page.get_attribute(".fwhsv-svg", "viewBox")
    page.click("button[data-z='in']")
    vb1 = page.get_attribute(".fwhsv-svg", "viewBox")
    assert float(vb1.split()[2]) < float(vb0.split()[2])
    page.click("button[data-z='fit']")
    assert page.get_attribute(".fwhsv-svg", "viewBox") == vb0
    ctx.close()


def test_a_phone_gets_the_portrait_layout(browser, base):
    ctx, page, _ = _page(browser, base, width=390, height=844)
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    assert page.get_attribute(".fwhsv-svg", "viewBox").split()[2] == "420"
    ctx.close()


def test_start_on_system_view_is_remembered(browser, base):
    ctx, page, _ = _page(browser, base)
    page.click("#open")
    page.check(".fwhsv-start input")
    page.goto(base + "/")
    page.wait_for_selector(".fwhsv-obj")
    assert page.locator(".fwhsv").is_visible()
    page.uncheck(".fwhsv-start input")
    page.click(".fwhsv-close")
    page.goto(base + "/")
    assert page.locator(".fwhsv").count() == 0 or page.locator(".fwhsv").is_hidden()
    ctx.close()


def test_an_outage_draws_the_grid_red(browser, base):
    ctx, page, _ = _page(browser, base, "?fixture=us_outage")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj[data-id='grid']")
    assert "s-crit" in page.get_attribute(".fwhsv-obj[data-id='grid']", "class")
    ctx.close()


@pytest.mark.parametrize("theme,dark", [("dark", True), ("light", False)])
def test_the_overlay_follows_the_host_pages_theme(browser, base, theme, dark):
    ctx, page, _ = _page(browser, base)
    page.evaluate(f"document.documentElement.dataset.theme = {theme!r}")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    bg = page.evaluate("getComputedStyle(document.querySelector('.fwhsv')).backgroundColor")
    r, g, b = [int(x) for x in bg[bg.index("(") + 1:bg.index(")")].split(",")[:3]]
    assert (r + g + b < 200) == dark, bg
    ctx.close()


def test_a_host_dialog_stays_above_the_overlay(browser, base):
    ctx, page, _ = _page(browser, base)
    page.evaluate("""() => { const d = document.createElement('div'); d.id = 'hostmodal';
      d.style.cssText = 'position:fixed;inset:30% 30%;z-index:50;background:#fff';
      document.body.appendChild(d); }""")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    top = page.evaluate("document.elementFromPoint(innerWidth / 2, innerHeight / 2).id")
    assert top == "hostmodal"
    ctx.close()


def test_the_overlay_starts_below_the_hosts_top_bar(browser, base):
    ctx, page, _ = _page(browser, base)
    page.evaluate("""() => { const h = document.querySelector('header');
      h.style.cssText += ';position:fixed;top:0;left:0;right:0;height:56px;z-index:50;background:#333'; }""")
    page.evaluate("FWHSystemView.close(); FWHSystemView.mount({endpoint: '/api/system', below: 'header'})")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    assert page.evaluate("document.querySelector('.fwhsv').getBoundingClientRect().top") == 56
    assert page.evaluate("document.elementFromPoint(innerWidth - 20, 80).closest('.fwhsv') !== null")
    ctx.close()


def test_the_overlay_ends_above_the_hosts_bottom_bar(browser, base):
    ctx, page, _ = _page(browser, base, width=390, height=844)
    page.evaluate("""() => { const n = document.createElement('nav'); n.id = 'tabs';
      n.style.cssText = 'position:fixed;bottom:0;left:0;right:0;height:60px;z-index:70;background:#333';
      document.body.appendChild(n); }""")
    page.evaluate("FWHSystemView.close(); FWHSystemView.mount({endpoint: '/api/system', above: '#tabs'})")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    assert page.evaluate("document.querySelector('.fwhsv').getBoundingClientRect().bottom") == 844 - 60
    ctx.close()


def test_the_strip_shows_the_site_and_the_weather(browser, base):
    ctx, page, errors = _page(browser, base)
    page.click("#open")
    page.wait_for_selector(".fwhsv-wx")
    assert "Los Angeles" in page.locator(".fwhsv-site").inner_text()
    assert "Partly cloudy" in page.locator(".fwhsv-wx").inner_text()
    assert errors == []
    ctx.close()


def test_customise_saves_and_the_diagram_follows(browser, base):
    ctx, page, errors = _page(browser, base, "?fixture=au_single_phase")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj[data-id='agate']")
    page.click(".fwhsv-cust")
    page.fill(".fwhsv-form input[placeholder='Example home']", "Beach house")
    page.select_option(".fwhsv-form select >> nth=0", "hidden")       # weather
    page.click(".fwhsv-save")
    page.wait_for_selector(".fwhsv-result.ok")
    assert "Saved" in page.locator(".fwhsv-result").inner_text()     # the result stays in the dialog
    assert page.locator(".fwhsv-dlg").is_visible()
    page.click(".fwhsv-cancel")
    assert "Beach house" in page.locator(".fwhsv-site").inner_text()
    assert errors == []
    ctx.close()


def test_a_refused_answer_is_shown_in_the_dialog(browser, base):
    ctx, page, _ = _page(browser, base, "?fixture=au_single_phase")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    page.click(".fwhsv-cust")
    page.fill(".fwhsv-form input >> nth=0", "x" * 61)
    page.click(".fwhsv-save")
    page.wait_for_selector(".fwhsv-result.err")
    assert "60 characters" in page.locator(".fwhsv-result").inner_text()
    ctx.close()


def test_a_full_battery_fits_inside_its_ring(browser, base):
    ctx, page, _ = _page(browser, base)
    page.click("#open")
    page.wait_for_selector(".fwhsv-soc")
    t = page.locator(".fwhsv-soc").bounding_box()
    r = page.locator(".fwhsv-ring0").bounding_box()
    assert t["width"] < r["width"] - 14          # inside the ring's stroke
    ctx.close()


def test_the_hover_text_sits_above_the_picture_not_over_its_label(browser, base):
    ctx, page, _ = _page(browser, base)
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj[data-id='home']")
    page.hover(".fwhsv-obj[data-id='home'] .fwhsv-big")
    tip = page.locator(".fwhsv-tip").bounding_box()
    big = page.locator(".fwhsv-obj[data-id='home'] .fwhsv-big").bounding_box()
    assert tip["y"] + tip["height"] <= big["y"]
    ctx.close()


def test_a_saved_answer_that_disagrees_with_a_reading_is_flagged_at_once(browser, base):
    ctx, page, _ = _page(browser, base, "?fixture=us_tou_two_apowers_solar")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    page.click(".fwhsv-cust")
    page.select_option(".fwhsv-form select >> nth=1", "L1")          # the aGate reads two legs
    page.click(".fwhsv-save")
    page.wait_for_selector(".fwhsv-result.ok")
    assert "the aGate reads 2" in page.locator(".fwhsv-mismatch").inner_text()
    ctx.close()


def test_the_shown_gateway_follows_the_hosts_picker_and_reports_back(browser, base):
    ctx, page, errors = _page(browser, base, "?fixture=two_gateways")
    page.evaluate("""() => { window.picked = []; FWHSystemView.mount({endpoint: '/api/system?fixture=two_gateways',
      gateway: () => 'gw2', onGateway: (id) => window.picked.push(id)}); }""")
    page.click("#open")
    page.wait_for_selector(".fwhsv-chips [aria-selected='true']")
    assert page.locator(".fwhsv-chips [aria-selected='true']").inner_text() == "Garage"     # opens on the host's
    page.evaluate("FWHSystemView.showGateway('gw1')")                                        # the host's picker moved
    assert page.locator(".fwhsv-chips [aria-selected='true']").inner_text() == "House"
    page.evaluate("FWHSystemView.showGateway('nope')")                                       # unknown: stays put
    assert page.locator(".fwhsv-chips [aria-selected='true']").inner_text() == "House"
    page.click(".fwhsv-chips [role=tab] >> text=Garage")
    assert page.evaluate("window.picked") == ["gw2"]                                         # the host is told
    assert errors == []
    ctx.close()


def test_a_tap_opens_the_details_and_leaves_no_tip_over_them(browser, base):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    page = ctx.new_page()
    page.goto(base + "/")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj[data-id='battery']")
    # What iOS Safari sends for a tap: a touch pointerenter, never a pointerleave, then a click.
    page.evaluate("""() => { const el = document.querySelector(".fwhsv-obj[data-id='battery']");
      const r = el.getBoundingClientRect();
      el.dispatchEvent(new PointerEvent("pointerenter", {pointerType: "touch", clientX: r.x + 5, clientY: r.y + 5}));
      el.dispatchEvent(new MouseEvent("click", {bubbles: true})); }""")
    page.wait_for_selector(".fwhsv-panel:not([hidden])")
    assert page.locator(".fwhsv-tip").is_hidden()
    page.tap(".fwhsv-pclose")
    assert page.locator(".fwhsv-panel").is_hidden()
    ctx.close()


def test_the_overlay_follows_the_hosts_top_bar_when_it_changes_height(browser, base):
    # A host's top bar can be taller while it loads (chips not yet hidden) and shrink after
    # the overlay opened; the overlay left an empty gap above itself.
    ctx, page, _ = _page(browser, base, width=390, height=844)
    page.evaluate("""() => { const h = document.querySelector('header');
      h.style.cssText += ';position:fixed;top:0;left:0;right:0;height:150px;z-index:50;background:#333'; }""")
    page.evaluate("FWHSystemView.close(); FWHSystemView.mount({endpoint: '/api/system', below: 'header'})")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    page.evaluate("document.querySelector('header').style.height = '56px'")
    page.wait_for_function("document.querySelector('.fwhsv').getBoundingClientRect().top === 56")
    ctx.close()


def test_a_phone_opens_with_the_view_options_folded_away(browser, base):
    ctx, page, _ = _page(browser, base, width=390, height=844)
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    assert page.locator("button[data-z='fit']").is_hidden()
    assert page.locator(".fwhsv-start").is_hidden()
    page.click(".fwhsv-opt")
    assert page.locator("button[data-z='fit']").is_visible()
    assert page.get_attribute(".fwhsv-opt", "aria-expanded") == "true"
    page.goto(base + "/")                                     # the choice is remembered
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    assert page.locator("button[data-z='fit']").is_visible()
    ctx.close()


def test_a_desktop_opens_with_the_view_options_shown(browser, base):
    ctx, page, _ = _page(browser, base)
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    assert page.locator("button[data-z='fit']").is_visible()
    page.click(".fwhsv-opt")
    assert page.locator("button[data-z='fit']").is_hidden()
    ctx.close()


def test_the_diagram_takes_most_of_a_phone_screen(browser, base):
    ctx, page, _ = _page(browser, base, width=390, height=844)
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    bar = page.locator(".fwhsv-bar").bounding_box()
    assert bar["height"] < 70                                 # one row: title, options, close
    ctx.close()


def test_a_host_with_its_own_picker_can_leave_the_gateway_chips_out(browser, base):
    ctx, page, _ = _page(browser, base, "?fixture=two_gateways")
    page.evaluate("""() => FWHSystemView.mount({endpoint: '/api/system?fixture=two_gateways',
      gateway: () => 'gw2', gatewayChips: false})""")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    assert page.locator(".fwhsv-chips button").count() == 0
    assert page.locator(".fwhsv-chips").is_hidden()
    ctx.close()


def test_reopening_starts_fitted_to_the_screen(browser, base):
    ctx, page, _ = _page(browser, base)
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    vb0 = page.get_attribute(".fwhsv-svg", "viewBox")
    page.click("button[data-z='in']")
    page.click(".fwhsv-close")
    page.click("#open")
    page.wait_for_selector(".fwhsv-obj")
    assert page.get_attribute(".fwhsv-svg", "viewBox") == vb0
    ctx.close()


def test_extras_are_switched_on_one_by_one_and_remembered(browser, base):
    """Owner, 2026-11-11: voltage and frequency, today's energy, power on the wires and
    alarms, each with its own switch under Options, off until switched on."""
    for width in (1280, 390):
        ctx, page, errors = _page(browser, base, "?fixture=us_tou_two_apowers_solar", width=width, height=844)
        page.click("#open")
        page.wait_for_selector(".fwhsv-obj[data-id='agate']")
        if page.locator(".fwhsv-bar.folded").count():
            page.click(".fwhsv-opt")
        vis = lambda sel: page.locator(sel).first.is_visible()      # noqa: E731
        assert not vis(".fwhsv-x-vhz") and not vis(".fwhsv-x-energy")
        assert not vis(".fwhsv-x-flow") and not vis(".fwhsv-x-alarms")
        for k, sel in (("vhz", ".fwhsv-x-vhz"), ("energy", ".fwhsv-x-energy"),
                       ("flow", ".fwhsv-flowlbl"), ("alarms", ".fwhsv-badge")):
            page.check(f"[data-show='{k}']")
            assert vis(sel), k
        assert "240.2 V · 60.00 Hz" in page.locator(".fwhsv-x-vhz").first.text_content()
        assert page.locator(".fwhsv-flowlbl").count() >= 3                  # home, solar, battery
        page.click(".fwhsv-obj[data-id='agate']")
        assert "Grid frequency out of range" in page.locator(".fwhsv-panel").text_content()
        page.reload()                                                   # reopens on #system
        if page.locator(".fwhsv").is_hidden():
            page.click("#open")
        page.wait_for_selector(".fwhsv-obj[data-id='agate']")
        assert vis(".fwhsv-x-energy") and vis(".fwhsv-badge")             # remembered
        page.evaluate("Object.keys(localStorage).filter(k => k.startsWith('fwh-system-view:show:')).forEach(k => localStorage.removeItem(k))")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert errors == []
        ctx.close()
