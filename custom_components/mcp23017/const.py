import voluptuous as vol
from homeassistant.helpers import config_validation as cv

"""Constants for MCP23017 integration."""
DOMAIN = "mcp23017"

PULL_MODE_UP = "up"
PULL_MODE_NONE = "none"

CONF_I2C_ADDRESS = "i2c_address"
CONF_I2C_BUS = "i2c_bus"
CONF_PINS = "pins"

CONF_INVERT_LOGIC = "invert_logic"
CONF_PULL_MODE = "pull_mode"
CONF_HW_SYNC = "hw_sync"
CONF_MOMENTARY = "momentary"
CONF_PULSE_TIME = "pulse_time"
CONF_SENSOR = "sensor"
CONF_PIN_NAME = "name"

CONF_FLOW_PLATFORM = "platform"
CONF_FLOW_PIN_NUMBER = "pin_number"
CONF_FLOW_PIN_NAME = "pin_name"

DEFAULT_SCAN_RATE = 0.1  # seconds
DEFAULT_I2C_BUS = 1  # use /dev/i2c-{DEFAULT_I2C_BUS}
DEFAULT_I2C_ADDRESS = 0x20

DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = PULL_MODE_UP
DEFAULT_HW_SYNC = True

DEFAULT_MOMENTARY = False
DEFAULT_PULSE_TIME = 200
# Bounds protect the relay coil: too short a pulse may not switch the relay,
# too long a pulse (e.g. a ms/s typo) overheats a coil rated for pulsed duty
MIN_PULSE_TIME = 50  # ms
MAX_PULSE_TIME = 5000  # ms
# Clamp instead of reject: an out-of-range value in an existing YAML config
# must not make the entities disappear after an upgrade
PULSE_TIME_CLAMP = vol.All(
    vol.Coerce(int), vol.Clamp(min=MIN_PULSE_TIME, max=MAX_PULSE_TIME)
)

CONF_DOUBLE_CLICK = "double_click"
CONF_DOUBLE_CLICK_WINDOW = "double_click_window"
CONF_EVENT_SUPPRESS_MARGIN = "event_suppress_margin"

DEFAULT_DOUBLE_CLICK = False
DEFAULT_DOUBLE_CLICK_WINDOW = 600  # ms
# Extra time added to the pulse time when suppressing sensor transitions
# caused by the integration's own pin actions; must exceed the worst-case
# feedback latency: relay switching + input polling + HA dispatch
DEFAULT_EVENT_SUPPRESS_MARGIN = 1000  # ms

# Schema for simple pin configuration (e.g., "0: setBi16")
_SIMPLE_PIN_SCHEMA = cv.string

# Schema for advanced pin configuration (e.g., "1: {name: lt_ogrod_kinkiet_taras, ...}")
_ADVANCED_PIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PIN_NAME): cv.string,
        vol.Optional(CONF_MOMENTARY, default=True): cv.boolean,
        vol.Optional(CONF_PULSE_TIME, default=DEFAULT_PULSE_TIME): PULSE_TIME_CLAMP,
        vol.Optional(CONF_SENSOR): cv.string,
        vol.Optional(CONF_DOUBLE_CLICK, default=DEFAULT_DOUBLE_CLICK): cv.boolean,
        vol.Optional(
            CONF_DOUBLE_CLICK_WINDOW, default=DEFAULT_DOUBLE_CLICK_WINDOW
        ): cv.positive_int,
        vol.Optional(
            CONF_EVENT_SUPPRESS_MARGIN, default=DEFAULT_EVENT_SUPPRESS_MARGIN
        ): cv.positive_int,
    }
)

# Combine simple and advanced pin schemas
_PIN_SCHEMA = vol.Any(_SIMPLE_PIN_SCHEMA, _ADVANCED_PIN_SCHEMA)

# Schema for the entire pins dictionary
_PINS_SCHEMA = vol.Schema({cv.positive_int: _PIN_SCHEMA})

# Base schema for MCP23017
MCP23017_BASE_SCHEMA = {
    vol.Required(CONF_PINS): _PINS_SCHEMA,
    vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
    vol.Optional(CONF_HW_SYNC, default=DEFAULT_HW_SYNC): cv.boolean,
    vol.Optional(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS): vol.Coerce(int),
    vol.Optional(CONF_I2C_BUS, default=DEFAULT_I2C_BUS): vol.Coerce(int),
}