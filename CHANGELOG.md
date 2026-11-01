# Changelog

## [0.1.0] — unreleased

### Added
- The System view overlay: grid, aGate, batteries (one card per unit, up to four, then
  "+N more"), solar arrays, home, smart circuits and generator, with live flows.
- Landscape and portrait layouts computed in Python (`scene`), so both bridges draw the same
  picture; zoom (− / Fit / +, pinch, Ctrl+wheel) and pan.
- Hover sentences, a details panel, state colours (normal, offline, warning, critical).
- "Start on System view", remembered per browser; `#system` opens it; Esc, Back or
  "Standard dashboard" closes it.
- Payload schema with `validate()`, `build()`, example payloads and a demo server.
