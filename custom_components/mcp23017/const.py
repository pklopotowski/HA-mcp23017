import voluptuous as vol
from homeassistant.helpers import config_validation as cv

"""Constants for MCP23017 integration."""
DOMAIN = "mcp23017"

MODE_UP = "UP"
MODE_DOWN = "NONE"

CONF_I2C_ADDRESS = "i2c_address"
CONF_I2C_BUS = "i2c_bus"
CONF_PINS = "pins"

CONF_INVERT_LOGIC = "invert_logic"
CONF_PULL_MODE = "pull_mode"
CONF_HW_SYNC = "hw_sync"

CONF_FLOW_PLATFORM = "platform"
CONF_FLOW_PIN_NUMBER = "pin_number"
CONF_FLOW_PIN_NAME = "pin_name"
CONF_MOMENTARY = "momentary"
CONF_PULSE_TIME = "pulse_time"
CONF_SENSOR = "sensor"
CONF_PIN_NAME = "name"

DEFAULT_SCAN_RATE = 0.1  # seconds
DEFAULT_I2C_BUS = 1  # use /dev/i2c-{DEFAULT_I2C_BUS}
DEFAULT_I2C_ADDRESS = 0x20

DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = MODE_UP
DEFAULT_HW_SYNC = True

DEFAULT_PULSE_TIME = 200

# Schema for simple pin configuration (e.g., "0: setBi16")
_SIMPLE_PIN_SCHEMA = cv.string

# Schema for advanced pin configuration (e.g., "1: {name: lt_ogrod_kinkiet_taras, ...}")
_ADVANCED_PIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PIN_NAME): cv.string,
        vol.Optional(CONF_MOMENTARY, default=True): cv.boolean,
        vol.Optional(CONF_PULSE_TIME, default=DEFAULT_PULSE_TIME): cv.positive_int,
        vol.Optional(CONF_SENSOR): cv.string,
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