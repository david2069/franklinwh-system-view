# Changelog

## [0.2.2] — unreleased

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
