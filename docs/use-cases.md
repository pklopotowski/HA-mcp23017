# Use Cases

Practical patterns for installations built on bistable relays with feedback
contacts (see the architecture diagram in the [README](../README.md)).

## 1. Light on a bistable relay, wall button in parallel

The baseline pattern: the wall push-button pulses the relay coil directly
(works with Home Assistant offline), and Home Assistant pulses the same coil
through an output pin. The feedback contact keeps the entity state correct no
matter who toggled the relay.

```yaml
light:
  - platform: mcp23017
    i2c_bus: 3
    i2c_address: 0x25
    pins:
      1:
        name: terrace_sconce
        sensor: binary_sensor.terrace_sconce
```

Result: `light.terrace_sconce` can be controlled from dashboards, scenes, and
automations; its state follows the physical relay within the input polling
interval (100 ms). `light.turn_on` on an already-on light is a safe no-op.

## 2. Gate / door opener (pulse without feedback)

A momentary output without a sensor emits a fixed-length pulse and returns to
`off` — suitable for gate controllers expecting a dry-contact impulse.

```yaml
switch:
  - platform: mcp23017
    i2c_bus: 3
    i2c_address: 0x24
    pins:
      0:
        name: gate_open
        momentary: true
        pulse_time: 200
      1:
        name: gate_close
        momentary: true
```

## 3. Continuous outputs (irrigation valves, DHW circulation)

The simple pin form is a plain on/off output holding its level — for solid
state relays that must stay energized while active.

```yaml
switch:
  - platform: mcp23017
    i2c_bus: 3
    i2c_address: 0x24
    pins:
      2: irrigation_terrace
      3: irrigation_laundry
      6: cwu_ground_floor
```

## 4. Double click toggles another circuit (blueprint, no YAML automation)

Enable detection on the pin, then pair the button with a target using the
bundled [`wall_button_action` blueprint](../blueprints/wall_button_action.yaml)
— two fields in the UI (Settings → Automations → Create with blueprint), full
automation traces, and rename-safe references. Example: double click on the
terrace sconce button toggles the terrace floodlight.

```yaml
light:
  - platform: mcp23017
    i2c_bus: 3
    i2c_address: 0x25
    pins:
      1:
        name: terrace_sconce
        sensor: binary_sensor.terrace_sconce
        double_click: true
```

Blueprint inputs: button event entity `event.terrace_sconce_button`,
press type `double`, action `light.toggle` on `light.terrace_floodlight`.

Note: a double click inherently blinks the primary light back to its original
state — the relay toggles on both presses. The gesture is the point, not the
intermediate state.

## 5. Double click drives a scene (automation on the event entity)

For richer reactions, trigger an automation from the `event` entity. Native
state trigger and native attribute condition — no templates:

```yaml
alias: "Terrace – wall button gestures"
description: >
  Double click on the terrace sconce button toggles the whole garden
  lighting group.
mode: single
triggers:
  - trigger: state
    entity_id: event.terrace_sconce_button
    not_from:
      - unknown
      - unavailable
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: event.terrace_sconce_button
            attribute: event_type
            state: "double"
        sequence:
          - action: light.toggle
            target:
              area_id: garden
```

## 6. Physical-usage insight from `single` events

Every wall press (filtered from HA-driven changes) emits a `single` event —
usable for presence heuristics, usage counters (via a `counter` helper), or
notifications, without any additional hardware.

## Tuning double-click detection on a live installation

1. Enable `double_click` on one pin and watch the `event` entity in the
   logbook.
2. Your double presses register as two `single` events → increase
   `double_click_window`; deliberate separate presses merge into `double` →
   decrease it.
3. False `single` events right after HA-driven switching → increase
   `event_suppress_margin`; wall presses ignored right after HA actions →
   decrease it (typical installations work at 300–500 ms).

All parameters live in the entity options and apply at runtime — no restart
required.
