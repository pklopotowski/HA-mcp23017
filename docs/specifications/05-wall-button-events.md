# Specification 05 — Wall-Button Press Events (Single / Double Click)

Introduced: v1.7.0

## Motivation

Wall push-buttons pulse the relay coil directly (hardware path, independent of
Home Assistant). The only signal visible to the integration is the relay
feedback contact. A single press produces one relay transition; two quick
presses produce two transitions in a short window. This is sufficient to
recognize *single* and *double* presses. A *long press* is not detectable with
this hardware: holding the button produces no additional transitions.

## Functional requirements

1. Sensor-tracked `switch`/`light` entries additionally expose an **`event`
   entity** (device class `button`, event types `single` and `double`),
   set up alongside the primary platform and removed with it.
2. **Own-action suppression:** sensor transitions caused by the integration's
   own pin actions are excluded from press detection. After each pin action,
   detection is suppressed for `pulse_time + event_suppress_margin`.
3. **Detection:**
   - detection counts only real `on`/`off` transitions (startup and
     `unavailable`/`unknown` transitions are ignored),
   - with `double_click` disabled, every wall-caused transition immediately
     emits `single`,
   - with `double_click` enabled, the first transition arms a timer of
     `double_click_window` ms; a second transition within the window emits
     `double`, expiry of the timer emits `single`.
4. **Orchestration stays in Home Assistant:** the integration only emits
   events. Reactions are defined by automations or the bundled
   `wall_button_action` blueprint on the event entity — no cross-entity
   action wiring inside the integration configuration (entity-id references
   stored in config-entry data would silently break on renames and bypass
   automation traces).
5. All parameters are configurable per pin in YAML and in the options flow,
   and are applied at runtime on options updates.
6. **Upgrade neutrality:** the YAML import includes the event-detection keys
   in the entry data only when a pin explicitly configures them (values
   differing from the defaults). Entries imported by earlier versions keep
   identical data, so upgrading does not reload existing entries on the
   first start.

## Configuration

| Option | Default | Description |
|---|---|---|
| `double_click` | `false` | enable window-based single/double discrimination |
| `double_click_window` | `600` ms | max spacing between the two transitions |
| `event_suppress_margin` | `1000` ms | added to `pulse_time` when suppressing own actions; production-tunable |

## Inherent behavior (hardware-driven)

- A double click toggles the relay twice: the light blinks and returns to its
  original state. A double click therefore acts as a *gesture*, not a state
  change.
- With `double_click` enabled, the `single` event is delayed by
  `double_click_window` — the cost of disambiguation.

## Tuning guidance

- False `single` events right after HA-driven switching → increase
  `event_suppress_margin`; wall presses ignored right after HA actions →
  decrease it. The margin must exceed relay switching time + input polling
  (100 ms) + Home Assistant dispatch latency.
- Double presses detected as two singles → increase `double_click_window`;
  distinct sequential presses merging into `double` → decrease it.
