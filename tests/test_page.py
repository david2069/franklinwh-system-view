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
