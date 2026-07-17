# Specification 04 — Hardware Safety for Pulsed Outputs

Introduced: v1.6.1

## Motivation

With the options dialog operational (v1.5.0) and entries stable (v1.6.0), two
previously unreachable code paths became reachable from the UI and could leave
the relay coil energized — a hardware hazard for coil drivers not rated for
continuous duty.

## Requirements and behavior

1. **Options update never re-drives a pulsed output.** After an options-flow
   save, a momentary output pin is forced to its inactive rest level and any
   pending turn-off callback is cancelled. Non-momentary outputs keep the
   previous behavior (logical state re-written with the new polarity).
2. **`turn_on` on an already-on, sensor-tracked relay is a no-op.** Another
   pulse would toggle the relay *off*; scenes and "turn everything on"
   automations must not invert states. (`turn_off` on an already-off entity
   was already a no-op.)
3. **Removal is clean.** `async_will_remove_from_hass`:
   - releases the sensor state listener (in the event loop — not from an
     executor thread),
   - cancels a pending pulse turn-off callback,
   - forces a momentary output to its inactive rest level, so an entry reload
     that lands mid-pulse cannot leave the coil energized.
4. **Device robustness.** Unregistering an entity from a pin with no
   registered entity logs a warning instead of raising.

## Rationale

The rest level of a pulsed output is `invert_logic` (logical *off*), matching
the level used by `configure_device` when `hw_sync` is disabled. Every path
that could leave the pin at the active level outside a timed pulse is treated
as a defect.
