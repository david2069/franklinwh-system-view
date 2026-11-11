# franklinwh-system-view

A friendly picture of a FranklinWH site, shared by the FranklinWH bridges: grid, aGate,
batteries, solar, home, smart circuits and generator, with live flows. It opens as a
full-page overlay over a bridge's own dashboard, and can be the page a browser starts on.

- **Simple by default.** Pictures and plain words: battery charge, mode, what the inverter
  is doing, grid up or down, solar, home use, circuits. Hover for a sentence, click for details.
- **Fits any screen.** Desktop and tablet get a landscape layout, phones a portrait one.
  Zoom with − / Fit / +, pinch, or Ctrl+wheel; drag to pan when zoomed. It always opens
  fitted. Zoom, Customise diagram and Start on sit under **Options**, folded on phones and
  shown on wider screens; the user's choice is remembered.
- **Extras, when wanted.** Under **Options** each has its own switch, off until switched on
  and remembered in the browser: **Voltage & frequency** under the grid, **Today's energy**
  (kWh) under each picture, **Power on wires** (the kW on each wire, with an arrow the way it
  goes) and **Alarms** (a count on the device; its details list them).
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

**A host with its own gateway picker** keeps it and the overlay on the same gateway:

```js
FWHSystemView.mount({endpoint: "api/system",
  gateway: () => picker.id,                 // shown when the overlay opens
  onGateway: (id) => picker.select(id)});   // the user picked a gateway in the overlay
picker.onChange((id) => FWHSystemView.showGateway(id));
```

With `gatewayChips: false` the overlay leaves out its own gateway chips and shows only the
gateway the host's picker has.

**Customise diagram.** Where no reading tells the bridge how a site is built, the user
tells it. The bridge stores the answers (one JSON object) and lets the package do the rest:

```python
raw = my_payload()
p = sv.customise.apply(raw, saved)                     # names, legs, models, solar, appliances
p["customise"] = {"endpoint": "api/system/customise", "fields": sv.customise.fields(raw, saved)}
return sv.build(p)

@app.put("/api/system/customise")
def save(values: dict):
    store(sv.customise.clean(values, my_payload()))   # ValueError → 400
```

With several gateways the dialog shows one at a time, from a **Gateway** picker that starts
on the gateway the diagram shows.

**Weather.** Put the current Open-Meteo reading in `site.weather` (`code`, `condition`,
`temp_c`); the page draws it next to the site's name.

The payload is described in `schema.py`; `fixtures/` holds examples. Signs: grid
`power_w` > 0 imports, battery `power_w` > 0 discharges. Leave out what you can't read.

Optional per gateway: `energy_today` (`grid_import_kwh`, `grid_export_kwh`, `solar_kwh`,
`home_kwh`, `battery_charge_kwh`, `battery_discharge_kwh`, each kWh or null) and `alarms`, a
list of `{target, unit?, code?, text, level}` where `target` is one of the objects (`grid`,
`agate`, `home`, `solar`, `battery`, `circuits`, `generator`), `unit` the 1-based battery or
circuit it is about, and `level` `warn` or `crit`. A value that is missing is not drawn.

## Try it

```bash
python -m franklinwh_system_view.demo us_tou_two_apowers_solar
```

Design: franklinwh-direct-connect-bridge #428.
