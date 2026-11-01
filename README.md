# franklinwh-system-view

A friendly picture of a FranklinWH site, shared by the FranklinWH bridges: grid, aGate,
batteries, solar, home, smart circuits and generator, with live flows. It opens as a
full-page overlay over a bridge's own dashboard, and can be the page a browser starts on.

- **Simple by default.** Pictures and plain words: battery charge, mode, what the inverter
  is doing, grid up or down, solar, home use, circuits. Hover for a sentence, click for details.
- **Fits any screen.** Desktop and tablet get a landscape layout, phones a portrait one.
  Zoom with − / Fit / +, pinch, or Ctrl+wheel; drag to pan when zoomed.
- **Colours mean state.** Green normal, grey offline or disabled, amber warning, red critical.
- **Only what's there is drawn.** A site with no solar shows no solar.

## How a bridge uses it

```python
from fastapi.staticfiles import StaticFiles
import franklinwh_system_view as sv

app.mount("/system-view", StaticFiles(directory=sv.static_dir()), name="system-view")

@app.get("/api/system")
def api_system():
    return sv.build(my_payload())      # validates, then adds both layouts per gateway
```

```html
<link rel="stylesheet" href="system-view/system-view.css">
<script src="system-view/system-view.js"></script>
<script>FWHSystemView.mount({endpoint: "api/system"});</script>
<button onclick="FWHSystemView.open()">System view</button>
```

The payload is described in `schema.py`; `fixtures/` holds examples. Signs: grid
`power_w` > 0 imports, battery `power_w` > 0 discharges. Leave out what you can't read.

## Try it

```bash
python -m franklinwh_system_view.demo us_tou_two_apowers_solar
```

Design: franklinwh-direct-connect-bridge #428.
