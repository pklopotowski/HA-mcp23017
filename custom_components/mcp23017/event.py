"""Wall-button event entity for MCP23017 sensor-tracked outputs."""

import logging

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    CONF_FLOW_PIN_NAME,
    CONF_FLOW_PIN_NUMBER,
    CONF_I2C_ADDRESS,
    CONF_I2C_BUS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a wall-button event entity for a sensor-tracked entry."""
    async_add_entities([MCP23017ButtonEvent(hass, config_entry)])


class MCP23017ButtonEvent(EventEntity):
    """Expose physical wall-button presses (single/double) as events.

    Presses are detected by the paired switch/light entity from the state
    transitions of its tracking sensor and forwarded via the dispatcher.
    """

    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = ["single", "double"]
    _attr_should_poll = False

    def __init__(self, hass, config_entry):
        """Initialize the event entity."""
        self._hass = hass
        self._entry_id = config_entry.entry_id
        self._i2c_bus = config_entry.data[CONF_I2C_BUS]
        self._i2c_address = config_entry.data[CONF_I2C_ADDRESS]
        self._pin_number = config_entry.data[CONF_FLOW_PIN_NUMBER]
        self._pin_name = config_entry.data[CONF_FLOW_PIN_NAME]

        self._attr_name = f"{self._pin_name} button"
        self._attr_unique_id = (
            f"{DOMAIN}:{self._i2c_bus}:0x{self._i2c_address:02x}"
            f"-0x{self._pin_number:02x}-button"
        )

    async def async_added_to_hass(self):
        """Subscribe to button events from the paired entity."""
        self.async_on_remove(
            async_dispatcher_connect(
                self._hass,
                f"{DOMAIN}_button_{self._entry_id}",
                self._handle_button_event,
            )
        )

    @callback
    def _handle_button_event(self, event_type):
        """Register a button press forwarded by the paired entity."""
        self._trigger_event(event_type)
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Attach to the same device as the paired entity."""
        return {
            "identifiers": {(DOMAIN, self._i2c_bus, self._i2c_address)},
            "manufacturer": "Microchip",
            "model": "MCP23017",
            "entry_type": DeviceEntryType.SERVICE,
        }
