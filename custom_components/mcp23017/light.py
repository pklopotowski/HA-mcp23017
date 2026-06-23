from homeassistant.components.light import (
    PLATFORM_SCHEMA as LIGHT_SCHEMA,
    LightEntity,
    ColorMode,  # Import ColorMode
)
from .mcp23017_entity import MCP23017Entity, _async_setup_platform, _async_setup_entry
from .const import MCP23017_BASE_SCHEMA

PLATFORM_SCHEMA = LIGHT_SCHEMA.extend(MCP23017_BASE_SCHEMA)

class MCP23017Light(MCP23017Entity, LightEntity):
    """Represent a light that uses MCP23017."""

    def __init__(self, hass, config_entry):
        """Initialize the MCP23017 light."""
        super().__init__(hass, config_entry)

    @property
    def icon(self):
        """Return device icon for this entity."""
        return "mdi:lightbulb"

    @property
    def supported_color_modes(self):
        """Define supported color modes"""
        return {ColorMode.ONOFF}

    @property
    def color_mode(self):
        """Return the current color mode"""
        return ColorMode.ONOFF

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the MCP23017 light platform."""
    await _async_setup_platform(hass, config, async_add_entities, "light")

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a MCP23017 light entry."""
    await _async_setup_entry(hass, config_entry, async_add_entities, MCP23017Light)