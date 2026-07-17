# Specification 01 — Bistable Relay Control (Pulsed Outputs with Sensor-Tracked State)

Introduced: v1.3.x (hassio line), refined through v1.6.1

## Motivation

Latching (bistable/impulse) relays such as the Hager EPN524 toggle on every
coil pulse and hold their contact position without power. A plain on/off GPIO
output cannot represent them: the output must emit a *pulse*, and the actual
relay position must be read back from a separate feedback contact, because
wall push-buttons can pulse the same coil without Home Assistant's knowledge.

## Functional requirements

1. A `switch` or `light` entity can operate in **momentary (pulsed)** mode:
   `turn_on`/`turn_off` set the output pin active, then return it to the
   inactive rest level after a configurable pulse time.
2. The entity state can be bound to a **tracking sensor** (`binary_sensor`
   reading the relay's feedback contact). When a sensor is configured, it is
   the single source of truth for `is_on`; the last commanded value is not.
3. A pending pulse must be cancellable: re-triggering while a pulse is in
   flight cancels the previous turn-off callback and schedules a new one.
4. `light` entities are first-class: `MCP23017Light` (color mode `ONOFF`)
   shares all behavior with `MCP23017Switch` via the `MCP23017Entity` base
   class (`mcp23017_entity.py`).

## Behavior

- `turn_on` / `turn_off` on a momentary entity both emit the same pulse — the
  relay toggles on any pulse; direction is determined by the relay itself.
- `turn_on` is skipped when the entity is already on and either has a tracking
  sensor or is non-momentary (see Specification 04).
- `turn_off` is skipped when the entity is already off.
- With a tracking sensor, `is_on` returns the sensor state; without one, it
  returns the last commanded state.
- Wall-button presses that toggle the relay outside Home Assistant are
  reflected through the tracking sensor with polling latency (default 100 ms).

## Configuration

YAML (advanced per-pin form; a plain string keeps the legacy simple form):

```yaml
light:
  - platform: mcp23017
    i2c_bus: 3
    i2c_address: 0x25
    pins:
      1:
        name: terrace_sconce
        momentary: true          # default true in the advanced form
        pulse_time: 200          # ms
        sensor: binary_sensor.terrace_sconce
```

| Option | Default | Description |
|---|---|---|
| `momentary` | `true` (advanced form) / `false` (simple form) | pulsed output |
| `pulse_time` | `200` ms | active-level duration of the pulse |
| `sensor` | — | entity id of the feedback `binary_sensor` |

All options are also editable per entity in the options flow (see
Specification 02 and 03 for precedence rules).

## Edge cases

- Sensor unavailable at startup → hardware pin state fallback (Spec 02).
- Entity removal mid-pulse → pin forced to rest level (Spec 04).
- Pulse time must exceed the relay's minimum impulse duration and the SSR
  switching time; 200 ms is a safe default for EPN524-class relays.
