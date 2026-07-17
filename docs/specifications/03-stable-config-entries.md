# Specification 03 — Stable Config Entries Across Restarts

Introduced: v1.6.0

## Motivation

The upstream YAML import flow removed and recreated the config entry of every
imported pin at each Home Assistant start. Entry IDs changed on every boot and
options configured from the UI were wiped, making UI-side tuning impossible.

## Functional requirements

1. `async_step_import` matches the existing entry by unique ID
   (`<domain>.<bus>.<address>.<pin>`) and **updates it in place**
   (`async_update_entry`) instead of removing and recreating it.
2. The entry is scheduled for reload (`async_schedule_reload`) **only when the
   imported YAML data actually differs** from the stored data; an unchanged
   YAML configuration causes no reload churn at startup.
3. Entry IDs are stable across restarts; entities, devices, and their history
   remain attached.
4. Options configured from the UI persist across restarts.

## Precedence rules

- **YAML** remains the source of *initial* values and fully defines new pins.
- For option-backed fields (`invert_logic`, `hw_sync`, `momentary`,
  `pulse_time`, `sensor`, wall-button event options), a value saved in the UI
  **takes precedence over YAML** once set, because options are no longer
  cleared at startup.
- To re-apply a YAML value for such a field, change it in the entity options,
  or remove the config entry and restart (the import recreates it from YAML).

## Verification

Confirmed on a production installation (80 entries): entry IDs identical
across consecutive restarts, no errors on startup, options preserved.
