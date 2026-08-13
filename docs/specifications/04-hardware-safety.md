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

## Fault-tolerance extensions

The initial revision covered the reachable UI paths; the following
requirements extend the guarantees to bus faults, restarts, and request
storms.

5. **I2C recovery resynchronizes the device.** Register writes update the
   driver cache first and are deduplicated against it, so a write dropped by
   a bus fault leaves the device out of sync — including a lost pulse
   turn-off, which keeps the coil energized while the driver believes the pin
   is off. On the first successful bus access after a fault, the IOCON
   register mapping, `OLAT`, `GPPU`, and `IODIR` are rewritten from cache
   (`OLAT` before `IODIR`, so a power-cycled device drives the correct level
   the moment a pin becomes an output). The resync aborts when the IOCON
   remap write is dropped (BANK=1 addresses would land on wrong registers of
   a BANK=0 device) and normalizes IOCON afterwards. During a fault the
   polling thread probes the bus when its input reads did not already touch
   it; a read that triggered a recovery is repeated with the restored
   mapping, so a wrong-register value from a power-cycled device is never
   consumed. The constructor suppresses recovery resyncs until the register
   cache exists. Independently of faults, the polling thread compares
   `IODIRA` — mapped at 0x00 in both BANK modes — against the cache every
   ~5 s, detecting a device that lost its configuration without any bus
   error (brown-out) and resynchronizing it.
6. **Safety writes bypass the cache dedup.** Every path that forces a
   momentary pin to its rest level (options update, removal, HA stop) writes
   the register unconditionally, so a stale cache cannot turn the forcing
   into a no-op.
7. **HA stop and start park pulsed outputs.** The pulse turn-off timer does
   not survive a Home Assistant stop, while the MCP23017 output latch does.
   On `EVENT_HOMEASSISTANT_STOP` a momentary output is forced to its rest
   level; at startup `configure_device` resets it regardless of `hw_sync`,
   covering a non-graceful shutdown that landed mid-pulse.
8. **Pulses cannot be extended.** A pulse request arriving while a pulse is
   active, or before an inter-pulse gap of one pulse time has elapsed, is
   dropped — logged at *warning* level, since a state-changing command was
   not executed — instead of restarting the turn-off timer. This bounds the
   coil duty cycle at 50% under repeated requests (automation loops, UI
   spam, sensor flapping). The guard is armed synchronously before the
   first `await` (pulse plus gap), so concurrent requests cannot slip
   through while the pin write is in the executor. A forced rest arms the
   gap only when it actually interrupted a pulse — an unrelated options
   save does not block subsequent pulses — and resets the tracked state of
   a sensor-less pin, so an interrupted pulse cannot leave the entity stuck
   ON.
9. **`pulse_time` is bounded to 50–5000 ms**: below the range the relay may
   not switch, above it a typo (ms vs s) overheats a coil rated for pulsed
   duty. The options flow rejects out-of-range input (the user is present to
   correct it); the YAML schema and the entity runtime *clamp* instead, so a
   pre-existing out-of-range value in an upgraded installation degrades to
   the nearest bound rather than breaking the config or bypassing the limit.
   The clamped value is persisted back to the config entry options.

## Rationale

The rest level of a pulsed output is `invert_logic` (logical *off*), matching
the level used by `configure_device`. Every path that could leave the pin at
the active level outside a timed pulse is treated as a defect.

## Limitations

The turn-off is a software timer on the event loop; a heavily loaded system
can stretch a pulse by seconds, and a hard host crash leaves the latch driven
until the MCP23017 loses power. Installations where an over-length pulse is
unacceptable need a hardware safeguard (a one-shot/monostable coil driver or
a coil rated for continuous duty).
