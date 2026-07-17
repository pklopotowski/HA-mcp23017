# HA-mcp23017

MCP23008/MCP23017 I2C I/O expander integration for Home Assistant — an
extended continuation of
[jpcornil-git/HA-mcp23017](https://github.com/jpcornil-git/HA-mcp23017),
enriched with bistable (latching/impulse) relay control, feedback-contact
state tracking, and wall-button press events.

Everything the original integration offers keeps working, including its
`configuration.yaml` syntax. The additions are opt-in, per pin.

## Highlights of the original implementation

All of the below comes from the excellent groundwork by
[Jean-Paul Cornil](https://github.com/jpcornil-git) and remains fully
supported:

- **Async** implementation (more reactive and nicer to HA)
- **Thread-safety** allowing different entities to use the same component
- **Config Flow** support (UI configuration) in addition to legacy
  configuration.yaml
- **Push iso pull model** for higher reactivity, e.g. 100 ms polling for
  'zero-delay' push buttons without loading HA
- Optimized I2C bus bandwidth utilisation (polling per device instead of per
  entity, register cache)
- I2C bus-error protection with single-shot error logging and recovery
  notification
- Synchronization with the device state at startup (no output glitches on HA
  restart)
- Compatible with **MCP23008** (8-pin variant), multiple **I2C busses**
- Translations (EN/FR/ES)

## What this continuation adds

- **`light` platform** alongside `switch` and `binary_sensor`
- **Pulsed (momentary) outputs** with configurable pulse time and cancellable
  turn-off — for bistable relays (e.g. Hager EPN524), gate openers, and other
  impulse-driven loads
- **Feedback state tracking**: an output entity can bind to a
  `binary_sensor` reading the relay's feedback contact — the entity state is
  always the physical relay position, even when wall push-buttons toggle the
  relay outside Home Assistant
- **Wall-button press events**: `single`/`double` presses recognized from the
  feedback transitions and exposed as `event` entities, with a bundled
  blueprint for pairing a press with an action in two UI fields
- **Stability and safety improvements** over the original implementation:
  stable config entries across restarts (UI options persist), options-flow
  compatibility with current Home Assistant releases, listener lifecycle
  cleanup, and hardware-safety guarantees for pulsed outputs (no code path
  leaves a relay coil energized) — see
  [docs/specifications](docs/specifications)

### How the bistable-relay model works

```
Home Assistant (RPi)
   │ I2C
   ▼
MCP23017 (outputs) ──► SSR ──► 24 V pulse ──► bistable relay coil ◄── wall push-buttons
                                                     │
                                        track 1: 230 V lighting circuit
                                        track 2: feedback contact
                                                     │
MCP23017 (inputs)  ◄─────────────────────────────────┘
   │
   └─► binary_sensor = the real relay state (source of truth)
```

## Installation

### HACS

1. HACS → ⋮ → *Custom repositories* → add
   `https://github.com/pklopotowski/HA-mcp23017` (type: *Integration*).
2. Download the latest release and restart Home Assistant.

### Manual

Copy `custom_components/mcp23017` into your configuration directory
(`/config/custom_components/mcp23017`) and restart Home Assistant.

> **Upgrading from jpcornil-git/HA-mcp23017:** drop-in — the integration
> domain and entry schema are unchanged, so existing config entries, entity
> IDs, and history are preserved. If the upstream repository is tracked in
> HACS, remove it there first so its updates do not overwrite this version.

## Configuration

### Classic outputs and inputs (as in the original integration)

```yaml
binary_sensor:
  - platform: mcp23017
    i2c_bus: 1
    i2c_address: 0x26
    pins:
      8: Button_0
      9: Button_1

switch:
  - platform: mcp23017
    i2c_bus: 2
    i2c_address: 0x26
    pins:
      0: Output_0
      1: Output_1
```

### Bistable relay outputs (advanced per-pin form)

```yaml
light:
  - platform: mcp23017
    i2c_bus: 3
    i2c_address: 0x25
    pins:
      1:
        name: terrace_sconce
        sensor: binary_sensor.terrace_sconce   # feedback contact
        # momentary: true                      # default in the advanced form
        # pulse_time: 200                      # ms
        # double_click: true

switch:
  - platform: mcp23017
    i2c_bus: 3
    i2c_address: 0x24
    pins:
      0:
        name: gate_open
        momentary: true        # pulse without feedback tracking
      2: irrigation_terrace    # simple form: plain on/off output
```

### Per-pin options

| Option | Default | Applies to | Description |
|---|---|---|---|
| `invert_logic` | `false` | all | invert pin polarity |
| `hw_sync` | `true` | switch/light | initial state from hardware |
| `pull_mode` | `up` | binary_sensor | internal pull-up resistor |
| `momentary` | `true`¹ | switch/light | pulsed output |
| `pulse_time` | `200` ms | switch/light | pulse duration |
| `sensor` | — | switch/light | feedback `binary_sensor` entity |
| `double_click` | `false` | switch/light | single/double press discrimination |
| `double_click_window` | `600` ms | switch/light | max spacing of a double click |
| `event_suppress_margin` | `1000` ms | switch/light | own-action suppression margin |

¹ `true` in the advanced (mapping) form, `false` in the simple form.

All options are also editable per entity in the UI (integration → entity →
*Configure*). Values saved in the UI persist across restarts and take
precedence over YAML for these fields; YAML defines new pins and initial
values. See [docs/specifications/03](docs/specifications/03-stable-config-entries.md).

## Wall-button events

Sensor-tracked outputs expose `event.<name>_button` with event types `single`
and `double`. See [docs/use-cases.md](docs/use-cases.md) for automation
examples and [docs/specifications/05](docs/specifications/05-wall-button-events.md)
for detection details and tuning.

## Documentation

- [Use cases](docs/use-cases.md)
- [Functional specifications](docs/specifications)

## Credits and license

- Original integration, I2C device core, and the foundations this project
  stands on: [Jean-Paul Cornil](https://github.com/jpcornil-git) —
  [HA-mcp23017](https://github.com/jpcornil-git/HA-mcp23017)
- Bistable-relay extensions, wall-button events, and maintenance of this
  continuation: [Piotr Klopotowski](https://github.com/pklopotowski)

Licensed under the [MIT License](LICENSE).
