# Specification 02 — Sensor Configuration and Listener Lifecycle

Introduced: v1.5.0

## Motivation

The tracking sensor (Specification 01) was originally configurable only from
YAML, its state listener was never released, and an unavailable sensor at
startup left the entity displaying `off` regardless of the physical relay
position.

## Functional requirements

1. The tracking sensor is configurable from the UI options flow of `switch`
   and `light` entries, using an `EntitySelector` restricted to the
   `binary_sensor` domain.
2. Changing the sensor at runtime re-subscribes the state listener: the old
   subscription is released, the new sensor is subscribed, and its current
   state is adopted immediately.
3. Options updates also refresh `momentary` and `pulse_time` at runtime
   (previously only `invert_logic` was applied without a restart).
4. The sensor state listener is released:
   - when the sensor is changed or cleared in the options flow,
   - when the entity is removed from Home Assistant
     (`async_will_remove_from_hass`, executed in the event loop).
5. When the configured sensor has no state at startup, the entity falls back
   to the hardware pin state (with a warning) instead of reporting `off`;
   the sensor takes over as soon as it reports.

## Behavior details

- `is_on` resolution order: sensor state (when a sensor is configured and has
  reported) → internal state (fallback/commanded).
- Clearing the sensor field disables sensor tracking at runtime; after a
  restart, a YAML-defined sensor is re-imported from the entry data (see
  Specification 03 for precedence).

## Non-goals

- Sensors from domains other than `binary_sensor` are not selectable; states
  other than `on` are treated as *off* (in particular `unavailable` and
  `unknown` never read as *on*).
