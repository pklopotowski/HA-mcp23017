from homeassistant.components.switch import PLATFORM_SCHEMA as SWITCH_SCHEMA, SwitchEntity
from .mcp23017_entity import MCP23017Entity, _async_setup_platform, _async_setup_entry
from .const import MCP23017_BASE_SCHEMA

PLATFORM_SCHEMA = SWITCH_SCHEMA.extend(MCP23017_BASE_SCHEMA)

class MCP23017Switch(MCP23017Entity, SwitchEntity):
    """Represent a switch that uses MCP23017."""

    def __init__(self, hass, config_entry):
        """Initialize the MCP23017 switch."""
        super().__init__(hass, config_entry)

    @property
    def icon(self):
        """Return device icon for this entity."""
        return "mdi:toggle-switch"

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the MCP23017 switch platform."""
    await _async_setup_platform(hass, config, async_add_entities, "switch")

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a MCP23017 switch entry."""
    await _async_setup_entry(hass, config_entry, async_add_entities, MCP23017Switch)