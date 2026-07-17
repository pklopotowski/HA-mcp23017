[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

# HA-mcp23017

MCP23008/MCP23017 I2C I/O expander integration — an extended continuation of
[jpcornil-git/HA-mcp23017](https://github.com/jpcornil-git/HA-mcp23017).
Everything the original offers keeps working; the additions are opt-in.

## Highlights of the original implementation

- **Async**, **thread-safe** implementation with **Config Flow** support
- **Push iso pull model** — 100 ms polling for 'zero-delay' push buttons
- Optimized I2C bandwidth (per-device polling, register cache), bus-error
  protection with recovery notification
- Device-state synchronization at startup, **MCP23008** compatible,
  multiple **I2C busses**

## What this continuation adds

- **`light` platform** and **pulsed (momentary) outputs** for bistable
  relays (e.g. Hager EPN524), gate openers, and impulse-driven loads
- **Feedback state tracking** from a `binary_sensor` — the entity state is
  the physical relay position, even when wall buttons bypass Home Assistant
- **Wall-button events** (`single`/`double`) as event entities, with a
  bundled blueprint for pairing a press with an action
- Stability and safety improvements: stable config entries across restarts,
  current-HA options flow, hardware-safety guarantees for pulsed outputs

## Useful links

- [Repository and documentation](https://github.com/pklopotowski/HA-mcp23017)
- [Original integration](https://github.com/jpcornil-git/HA-mcp23017)
- [MCP23017 device](https://www.microchip.com/wwwproducts/en/mcp23017)
