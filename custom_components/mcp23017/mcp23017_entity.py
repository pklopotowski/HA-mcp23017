"""Base class for MCP23017 entities."""

import functools
import logging

from . import async_get_or_create
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event, async_call_later

from .const import (
    CONF_FLOW_PIN_NAME,
    CONF_FLOW_PIN_NUMBER,
    CONF_FLOW_PLATFORM,
    CONF_I2C_ADDRESS,
    CONF_I2C_BUS,
    CONF_INVERT_LOGIC,
    CONF_HW_SYNC,
    CONF_PINS,
    CONF_MOMENTARY,
    CONF_PULSE_TIME,
    CONF_SENSOR,
    CONF_PIN_NAME,
    CONF_DOUBLE_CLICK,
    CONF_DOUBLE_CLICK_WINDOW,
    CONF_EVENT_SUPPRESS_MARGIN,
    DEFAULT_I2C_ADDRESS,
    DEFAULT_I2C_BUS,
    DEFAULT_INVERT_LOGIC,
    DEFAULT_HW_SYNC,
    DEFAULT_PULSE_TIME,
    DEFAULT_DOUBLE_CLICK,
    DEFAULT_DOUBLE_CLICK_WINDOW,
    DEFAULT_EVENT_SUPPRESS_MARGIN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def _async_setup_platform(hass, config, async_add_entities, platform):
    """Set up the MCP23017 platform for a specific entity type."""
    for pin_number, pin_config in config[CONF_PINS].items():
        if isinstance(pin_config, dict):
            # Advanced configuration
            pin_name = pin_config[CONF_PIN_NAME]
            momentary = pin_config[CONF_MOMENTARY]
            pulse_time = pin_config[CONF_PULSE_TIME]
            sensor = pin_config.get(CONF_SENSOR)
            double_click = pin_config[CONF_DOUBLE_CLICK]
            double_click_window = pin_config[CONF_DOUBLE_CLICK_WINDOW]
            event_suppress_margin = pin_config[CONF_EVENT_SUPPRESS_MARGIN]
        else:
            # Simple configuration
            pin_name = pin_config
            momentary = False
            pulse_time = DEFAULT_PULSE_TIME
            sensor = None
            double_click = DEFAULT_DOUBLE_CLICK
            double_click_window = DEFAULT_DOUBLE_CLICK_WINDOW
            event_suppress_margin = DEFAULT_EVENT_SUPPRESS_MARGIN

        data = {
            CONF_FLOW_PLATFORM: platform,
            CONF_FLOW_PIN_NUMBER: pin_number,
            CONF_FLOW_PIN_NAME: pin_name,
            CONF_I2C_ADDRESS: config[CONF_I2C_ADDRESS],
            CONF_I2C_BUS: config[CONF_I2C_BUS],
            CONF_INVERT_LOGIC: config[CONF_INVERT_LOGIC],
            CONF_HW_SYNC: config[CONF_HW_SYNC],
            CONF_MOMENTARY: momentary,
            CONF_PULSE_TIME: pulse_time,
            CONF_SENSOR: sensor,
        }
        # Include the event-detection keys only when the pin actually
        # configures them: entries imported by older versions keep
        # identical data, so an upgrade does not reload every entry on
        # the first start
        if double_click != DEFAULT_DOUBLE_CLICK:
            data[CONF_DOUBLE_CLICK] = double_click
        if double_click_window != DEFAULT_DOUBLE_CLICK_WINDOW:
            data[CONF_DOUBLE_CLICK_WINDOW] = double_click_window
        if event_suppress_margin != DEFAULT_EVENT_SUPPRESS_MARGIN:
            data[CONF_EVENT_SUPPRESS_MARGIN] = event_suppress_margin

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=data,
            )
        )

async def _async_setup_entry(hass, config_entry, async_add_entities, entity_class):
    """Set up a MCP23017 entity from a config entry."""
    entity = entity_class(hass, config_entry)
    entity.device = await async_get_or_create(hass, config_entry, entity)

    if await hass.async_add_executor_job(entity.configure_device):
        async_add_entities([entity])

class MCP23017Entity:
    """Base class for MCP23017 entities."""

    def __init__(self, hass, config_entry):
        """Initialize the MCP23017 base entity."""
        self._device = None
        self._state = None
        self._unsub_turn_off = None
        self._unsubscribe_sensor = None
        self._hass = hass

        self._i2c_address = config_entry.data[CONF_I2C_ADDRESS]
        self._i2c_bus = config_entry.data[CONF_I2C_BUS]
        self._pin_name = config_entry.data[CONF_FLOW_PIN_NAME]
        self._pin_number = config_entry.data[CONF_FLOW_PIN_NUMBER]
        self._invert_logic = config_entry.options.get(
            CONF_INVERT_LOGIC,
            config_entry.data.get(CONF_INVERT_LOGIC, DEFAULT_INVERT_LOGIC)
        )
        self._hw_sync = config_entry.options.get(
            CONF_HW_SYNC,
            config_entry.data.get(CONF_HW_SYNC, DEFAULT_HW_SYNC)
        )
        self._momentary = config_entry.options.get(
            CONF_MOMENTARY,
            config_entry.data.get(CONF_MOMENTARY, False)
        )
        self._pulse_time = config_entry.options.get(
            CONF_PULSE_TIME,
            config_entry.data.get(CONF_PULSE_TIME, DEFAULT_PULSE_TIME)
        )
        self._sensor = config_entry.options.get(
            CONF_SENSOR,
            config_entry.data.get(CONF_SENSOR, None)
        )
        self._sensor_state = None
        self._double_click = config_entry.options.get(
            CONF_DOUBLE_CLICK,
            config_entry.data.get(CONF_DOUBLE_CLICK, DEFAULT_DOUBLE_CLICK)
        )
        self._double_click_window = config_entry.options.get(
            CONF_DOUBLE_CLICK_WINDOW,
            config_entry.data.get(
                CONF_DOUBLE_CLICK_WINDOW, DEFAULT_DOUBLE_CLICK_WINDOW
            )
        )
        self._event_suppress_margin = config_entry.options.get(
            CONF_EVENT_SUPPRESS_MARGIN,
            config_entry.data.get(
                CONF_EVENT_SUPPRESS_MARGIN, DEFAULT_EVENT_SUPPRESS_MARGIN
            )
        )
        self._entry_id = config_entry.entry_id
        self._suppress_events_until = 0.0
        self._click_timer_cancel = None

        # Create or update option values for the platform
        hass.config_entries.async_update_entry(
            config_entry,
            options={
                CONF_INVERT_LOGIC: self._invert_logic,
                CONF_HW_SYNC: self._hw_sync,
                CONF_MOMENTARY: self._momentary,
                CONF_PULSE_TIME: self._pulse_time,
                CONF_SENSOR: self._sensor,
                CONF_DOUBLE_CLICK: self._double_click,
                CONF_DOUBLE_CLICK_WINDOW: self._double_click_window,
                CONF_EVENT_SUPPRESS_MARGIN: self._event_suppress_margin,
            },
        )

        # Subscribe to updates of config entry options
        self._unsubscribe_update_listener = config_entry.add_update_listener(
            self.async_config_update
        )

        _LOGGER.debug(
            "%s(pin %d:'%s') created",
            type(self).__name__,
            self._pin_number,
            self._pin_name,
        )

    async def async_added_to_hass(self):
        """Register callbacks and initialize state."""
        if self._sensor:
            self._subscribe_sensor()
            # Fetch initial sensor state
            sensor_state = self._hass.states.get(self._sensor)
            if sensor_state:
                self._sensor_state = sensor_state.state
                self._state = self._sensor_state == 'on'
            else:
                _LOGGER.warning(
                    f"Sensor {self._sensor} not found, "
                    f"using hardware state for {self._pin_name}."
                )
                self._state = await self._hass.async_add_executor_job(
                    self._device.get_pin_value, self._pin_number
                ) ^ self._invert_logic
        else:
            # Initialize state based on device pin value
            self._state = await self._hass.async_add_executor_job(
                self._device.get_pin_value, self._pin_number
            ) ^ self._invert_logic

        # Write initial state to Home Assistant
        self.async_write_ha_state()

    def _subscribe_sensor(self):
        """Subscribe to state changes of the configured sensor."""
        self._unsubscribe_sensor = async_track_state_change_event(
            self._hass, self._sensor, self._async_sensor_changed
        )

    def _unsubscribe_sensor_if_exists(self):
        """Unsubscribe from sensor state changes."""
        if self._unsubscribe_sensor:
            self._unsubscribe_sensor()
            self._unsubscribe_sensor = None

    async def async_will_remove_from_hass(self):
        """Clean up subscriptions and pending timers before removal."""
        self._unsubscribe_sensor_if_exists()
        await self._async_cancel_turn_off_callback_if_exists()
        if self._click_timer_cancel:
            self._click_timer_cancel()
            self._click_timer_cancel = None
        if self._momentary:
            # Leave a pulsed output at its inactive level so a removal in
            # the middle of a pulse cannot keep the relay coil energized
            await self._hass.async_add_executor_job(
                functools.partial(
                    self._device.set_pin_value,
                    self._pin_number,
                    self._invert_logic,
                )
            )

    async def _async_sensor_changed(self, event):
        """Handle binary sensor state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        old_state = self._sensor_state
        self._sensor_state = new_state.state
        self.async_write_ha_state()

        # Wall-button press detection: count only real on/off transitions
        # that were not caused by our own pin action
        if new_state.state not in ("on", "off") or new_state.state == old_state:
            return
        if old_state not in ("on", "off"):
            return
        if self._hass.loop.time() < self._suppress_events_until:
            return

        if not self._double_click:
            self._fire_button_event("single")
            return

        if self._click_timer_cancel:
            # Second transition within the window: double click
            self._click_timer_cancel()
            self._click_timer_cancel = None
            self._fire_button_event("double")
        else:
            self._click_timer_cancel = async_call_later(
                self._hass,
                self._double_click_window / 1000.0,
                self._async_click_timeout,
            )

    async def _async_click_timeout(self, _):
        """No second transition arrived within the window: single press."""
        self._click_timer_cancel = None
        self._fire_button_event("single")

    def _fire_button_event(self, event_type):
        """Notify the event entity about a wall-button press."""
        async_dispatcher_send(
            self._hass, f"{DOMAIN}_button_{self._entry_id}", event_type
        )

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._device.unique_id}-0x{self._pin_number:02x}"

    @property
    def name(self):
        """Return the name of the entity."""
        return self._pin_name

    @property
    def is_on(self):
        """Return true if the entity is on, based on the binary sensor state."""
        if self._sensor and self._sensor_state is not None:
            return self._sensor_state == "on"
        return self._state

    @property
    def pin(self):
        """Return the pin number of the entity."""
        return self._pin_number

    @property
    def address(self):
        """Return the i2c address of the entity."""
        return self._i2c_address

    @property
    def bus(self):
        """Return the i2c bus of the entity."""
        return self._i2c_bus

    @property
    def device_info(self):
        """Device info."""
        return {
            "identifiers": {(DOMAIN, self._i2c_bus, self._i2c_address)},
            "manufacturer": "Microchip",
            "model": "MCP23017",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def device(self):
        """Get device property."""
        return self._device

    @device.setter
    def device(self, value):
        """Set device property."""
        self._device = value

    async def _async_set_pin_value(self, value):
        """
        Set the pin value and update the state.
        :param value: Desired logical state (True for on, False for off).
        """
        # Sensor transitions caused by our own pin action must not be
        # counted as wall-button presses
        self._suppress_events_until = (
            self._hass.loop.time()
            + (self._pulse_time + self._event_suppress_margin) / 1000.0
        )
        try:
            # Apply invert_logic to the value before setting the pin
            pin_value = not value if self._invert_logic else value
            await self.hass.async_add_executor_job(
                functools.partial(self._device.set_pin_value, self._pin_number, pin_value)
            )
            if not self._sensor:
                self._state = value
            self.async_write_ha_state()
            _LOGGER.debug(f"{self._pin_name} set to {value} (invert_logic: {self._invert_logic}).")
        except Exception as e:
            _LOGGER.error(f"Failed to set {self._pin_name} to {value}: {e}")

    async def _async_handle_turn_off(self, _):
        """Callback to turn off the switch after the pulse time."""
        await self._async_set_pin_value(False)
        self._unsub_turn_off = None 

    async def _async_schedule_turn_off(self):
        """Schedule the turn-off callback after the pulse time."""
        self._unsub_turn_off = async_call_later(
            self.hass,
            self._pulse_time / 1000.0,  # Convert milliseconds to seconds
            self._async_handle_turn_off  # Callback to turn off the switch
        )
        _LOGGER.debug(f"{self._pin_name} scheduled to turn off in {self._pulse_time} ms.")

    async def _async_cancel_turn_off_callback_if_exists(self):
        """Cancel any scheduled turn-off callback."""
        if self._unsub_turn_off:
            self._unsub_turn_off()
            self._unsub_turn_off = None
            _LOGGER.debug(f"{self._pin_name} turn-off callback cancelled.")

    async def _async_toggle_momentary_switch(self):
        """Toggle a momentary switch on and off after the pulse time."""
        await self._async_cancel_turn_off_callback_if_exists()
        await self._async_set_pin_value(True)  # Turn on
        await self._async_schedule_turn_off()

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        # Skip when already on: for a sensor-tracked bistable relay another
        # pulse would toggle it back off
        if self.is_on and (self._sensor or not self._momentary):
            _LOGGER.debug(f"{self._pin_name} is already on. Skipping.")
            return

        if self._momentary:
            await self._async_toggle_momentary_switch()
        else:
            await self._async_set_pin_value(True)

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        if not self.is_on:
            _LOGGER.debug(f"{self._pin_name} is already off. Skipping.")
            return

        if self._momentary:
            await self._async_toggle_momentary_switch()
        else:
            await self._async_set_pin_value(False)

    async def async_config_update(self, hass, config_entry):
        """Handle update from config entry options."""
        self._invert_logic = config_entry.options[CONF_INVERT_LOGIC]
        self._momentary = config_entry.options.get(CONF_MOMENTARY, self._momentary)
        self._pulse_time = config_entry.options.get(CONF_PULSE_TIME, self._pulse_time)
        self._double_click = config_entry.options.get(
            CONF_DOUBLE_CLICK, self._double_click
        )
        self._double_click_window = config_entry.options.get(
            CONF_DOUBLE_CLICK_WINDOW, self._double_click_window
        )
        self._event_suppress_margin = config_entry.options.get(
            CONF_EVENT_SUPPRESS_MARGIN, self._event_suppress_margin
        )

        new_sensor = config_entry.options.get(CONF_SENSOR)
        if new_sensor != self._sensor:
            self._unsubscribe_sensor_if_exists()
            self._sensor = new_sensor
            self._sensor_state = None
            if self._sensor:
                self._subscribe_sensor()
                sensor_state = hass.states.get(self._sensor)
                if sensor_state:
                    self._sensor_state = sensor_state.state

        if self._momentary:
            # Pulsed output: never re-drive the tracked state onto the pin,
            # its rest level must stay inactive
            await self._async_cancel_turn_off_callback_if_exists()
            await hass.async_add_executor_job(
                functools.partial(
                    self._device.set_pin_value,
                    self._pin_number,
                    self._invert_logic,
                )
            )
        else:
            await hass.async_add_executor_job(
                functools.partial(
                    self._device.set_pin_value,
                    self._pin_number,
                    self._state ^ self._invert_logic,
                )
            )
        self.async_schedule_update_ha_state()

    def unsubscribe_update_listener(self):
        """Remove listener from config entry options."""
        self._unsubscribe_update_listener()

    def configure_device(self):
        """Attach instance to a device on the given address and configure it.

        This function should be called from the thread pool as it contains blocking functions.

        Return True when successful.
        """
        if self.device:
            # Reset pin value when HW sync is not required
            if not self._hw_sync:
                self._device.set_pin_value(self._pin_number, self._invert_logic)
            # Configure entity as output
            self._device.set_input(self._pin_number, False)
            self._state = self._device.get_pin_value(self._pin_number) ^ self._invert_logic

            return True

        return False