# Changelog

## [0.5.1] — 2026-11-19

### Fixed
- **Solar forecast & actual on a phone:** the three figures sit side by side, each label
  over its value, instead of wrapping mid-label ("Actual so / far").

## [0.5.0] — 2026-11-19

### Added
- **Solar forecast & actual** under **Options** (owner, Direct Connect Bridge). Off until
  switched on and remembered in the browser. A box on the diagram's left (above it on a
  phone) shows today's forecast, the actual so far, what is still to come and a bar of
  actual against forecast. It comes from a new optional per-gateway `solar_forecast`
  (`forecast_kwh`, `actual_kwh`, `remaining_kwh`), the bridge's own forecast. A bridge that
  sends none shows no box.

### Fixed
- **iPhone in Home Assistant: a blank band under the host's top bar.** The overlay padded its
  top by the notch inset, which a frame reports too, though it sat below the host's bar. Between a
  host's bars (`below` / `above`), it now leaves those insets to the bars.
- **Fit didn't fit a site's diagram on a phone.** It opens as wide as the screen and scrolls
  down; **Fit**, or − from there, now shows it whole, and + goes back to full width. Before,
  − stopped at the scrolled size and Fit did nothing.

## [0.4.1] — 2026-11-17

### Added
- **Battery roll-up** (owner, Direct Connect Bridge #703; #11). With `battery.rollup: true`
  and `units`, several aPowers are drawn as one battery: the gateway's charge and power as
  the aGate reports them, labelled *Batteries ×N*. The hover has a line per aPower (charge,
  current, state) and the details a row per aPower (with state of health). A unit's warning
  or fault colours the one battery, and a unit's alarm is listed on it. Without `rollup` the
  per-unit cards are drawn as before. Hover text and details now keep their line breaks.

## [0.4.0] — 2026-11-16

### Added
- **One diagram for a site with several gateways** (owner, Direct Connect Bridge #662), laid
  out after board E of the owner's design, as the FranklinWH emulator draws a grouped site.
  A gateway may name its site in a new optional `site` field (`id`, `name`, and the service
  `meter` it is fed through: `id`, `name`, `ac` `single`/`split`/`three`, `rated_amps`). When
  two or more gateways name the same site, `build()` adds `site_groups`: each with its
  `gateway_ids` and its own scenes (landscape, portrait and both without the smart
  circuits). The grid and the service meter are on the left, then one row per aGate fed by
  its own line: its batteries under it, its solar, generator, smart circuits and home to the
  right. The grid shows the site's total (unknown when one aGate's is) and each aGate's
  figure in its details; the meter is drawn only when every gateway names the same one.
- The page draws the site's diagram whenever the shown gateway belongs to such a site, with
  that gateway's aGate, name and line in cyan, and the site's name in the strip. Tapping
  another aGate shows that gateway and calls `onGateway`, so the host's picker follows.
  On a phone the site's diagram is as wide as the screen and scrolls down. A gateway alone
  on its site, or with no `site`, is drawn as before.

## [0.3.2] — 2026-11-16

### Changed
- **Options is a drop-down** (owner, Direct Connect Bridge #660). Zoom, Customise diagram, the
  extras and Start on open over the diagram, so it no longer moves; it starts closed and closes
  on a click outside it or Esc (Esc then closes the overlay). Before, the controls were a row
  under the toolbar, shown on wide screens and remembered.

### Added
- **Smart circuits** under Options: shown until switched off, remembered in the browser.
  `build()` adds `landscape_no_circuits` and `portrait_no_circuits` scenes when a gateway has
  circuits, laid out again without them; `scene(..., circuits=False)` makes one.

## [0.3.1] — 2026-11-12

### Changed
- **Customise diagram: one gateway at a time** (owner, Direct Connect Bridge). With several
  gateways, a **Gateway** picker at the top shows one gateway's settings, starting on the one
  the diagram shows; the site's settings stay above it. Before, every gateway was listed,
  one under the other.

## [0.3.0] — 2026-11-11

### Added
- Four extras under **Options**, each with its own switch, off until switched on and
  remembered in the browser (owner, Direct Connect Bridge):
  - **Voltage & frequency** under the grid (`grid.voltage_v`, `grid.freq_hz`, already in the
    payload but not drawn).
  - **Today's energy** in kWh under the grid (in and out), solar, home and the battery card,
    from a new optional `energy_today`.
  - **Power on wires**: the kW on each wire, by its longest straight run, with an arrow the way
    the power goes.
  - **Alarms**: a new optional `alarms` list; a count on the device's corner (amber warning,
    red critical) and the list in its details.
  Each picture keeps a line free for its extras, so switching one on doesn't move the wires.

## [0.2.4] — 2026-11-07

### Added
- `mount({gatewayChips: false})`: a host with its own gateway picker can leave the overlay's
  gateway chips out, so the gateway is chosen in one place.

### Changed
- Zoom, Customise diagram and Start on are under an **Options** button: folded on phones,
  shown on wider screens, and the user's choice is remembered. On a phone they took more
  room than the diagram. On a phone the close button shows ✕ only.
- The overlay always opens fitted to the screen; a zoom from last time is not kept.

### Fixed
- The overlay follows the host's top and bottom bars when they change height after it
  opened. A top bar that was taller while loading left an empty gap above the overlay.

## [0.2.3] — unreleased

### Fixed
- On a phone, a tap left the object's hover box on screen, covering the details panel's ✕
  ("Can't dismiss this view", iPhone Safari). A touch no longer shows the hover box, and
  opening the details hides it. Reported by the Modbus Bridge session.

## [0.2.2] — 2026-11-01

### Added
- `mount({gateway, onGateway})` and `FWHSystemView.showGateway(id)`, so a host's gateway
  picker and the overlay's gateway chips show the same gateway. Without them the overlay
  could show one gateway while the host's picker said another. Reported by the Modbus
  Bridge.
- A two-gateway example payload (`two_gateways`).

## [0.2.1] — 2026-11-01

### Fixed
- An object in `unavailable` is drawn grey, "Not available here", as the design says. It
  was left out (the grid) or ignored (the others). Reported by the Modbus Bridge review.
- A smart circuit in an unknown state said "Off" in its details; it says "Unknown".

## [0.2.0] — 2026-11-01

### Added
- **Customise diagram** (`customise.fields`, `apply`, `clean`, and a dialog on the page). The
  user names the site, each gateway and each smart circuit, and sets the service legs, the
  battery model, where solar connects, whether a generator is fitted, a picture for each
  smart circuit (heating/cooling, hot water, EV, pool, other) and whether weather shows.
  Where a reading exists it is shown beside the answer; a mismatch is flagged in the form,
  never silently overridden. A catalogue guess pre-fills a field marked "please confirm".
  The save's result stays in the dialog.
- **Site strip** above the diagram: the site's name and the weather now, from a WMO code,
  as one of nine pictures (sun, part cloud, cloud, fog, light rain, rain, heavy rain, snow,
  storm).
- Solar or a generator added in Customise but not reported by the aGate is drawn grey,
  "Not reported".

### Fixed
- "100%" no longer spills outside the battery ring.
- The hover text sits above the pointer, so it no longer covers the label and value under
  the picture.

## [0.1.0] — 2026-11-01

### Added
- The System view overlay: grid, aGate, batteries (one card per unit, up to four, then
  "+N more"), solar arrays, home, smart circuits and generator, with live flows.
- Landscape and portrait layouts computed in Python (`scene`), so both bridges draw the same
  picture; zoom (− / Fit / +, pinch, Ctrl+wheel) and pan.
- Hover sentences, a details panel, state colours (normal, offline, warning, critical).
- "Start on System view", remembered per browser; `#system` opens it; Esc, Back or
  "Standard dashboard" closes it.
- Payload schema with `validate()`, `build()`, example payloads and a demo server.
