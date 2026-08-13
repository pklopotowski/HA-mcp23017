"""Config flow for MCP23017 component."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from . import i2c_device_exist
from .const import (
    CONF_FLOW_PIN_NAME,
    CONF_FLOW_PIN_NUMBER,
    CONF_FLOW_PLATFORM,
    CONF_I2C_ADDRESS,
    CONF_I2C_BUS,
    CONF_INVERT_LOGIC,
    CONF_PULL_MODE,
    CONF_HW_SYNC,
    CONF_MOMENTARY,
    CONF_PULSE_TIME,
    CONF_SENSOR,
    CONF_DOUBLE_CLICK,
    CONF_DOUBLE_CLICK_WINDOW,
    CONF_EVENT_SUPPRESS_MARGIN,
    DEFAULT_I2C_ADDRESS,
    DEFAULT_I2C_BUS,
    DEFAULT_INVERT_LOGIC,
    DEFAULT_PULL_MODE,
    DEFAULT_HW_SYNC,
    DEFAULT_MOMENTARY,
    DEFAULT_PULSE_TIME,
    DEFAULT_DOUBLE_CLICK,
    DEFAULT_DOUBLE_CLICK_WINDOW,
    DEFAULT_EVENT_SUPPRESS_MARGIN,
    MIN_PULSE_TIME,
    MAX_PULSE_TIME,
    DOMAIN,
    PULL_MODE_NONE,
    PULL_MODE_UP,
)

PLATFORMS = ["binary_sensor", "switch", "light"]


class Mcp23017ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """MCP23017 config flow."""

    VERSION = 3
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def _title(self, user_input):
        return "Bus: %d, address: 0x%02x, pin: %d ('%s':%s)" % (
            user_input[CONF_I2C_BUS],
            user_input[CONF_I2C_ADDRESS],
            user_input[CONF_FLOW_PIN_NUMBER],
            user_input[CONF_FLOW_PIN_NAME],
            user_input[CONF_FLOW_PLATFORM],
        )

    def _unique_id(self, user_input):
        return "%s.%d.%d.%d" % (
            DOMAIN,
            user_input[CONF_I2C_BUS],
            user_input[CONF_I2C_ADDRESS],
            user_input[CONF_FLOW_PIN_NUMBER],
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Add support for config flow options."""
        return Mcp23017OptionsFlowHandler()

    async def async_step_import(self, user_input=None):
        """Create or update an entity from configuration.yaml import."""

        config_entry = await self.async_set_unique_id(self._unique_id(user_input))
        # Update entry (from storage) matching the same unique id, keeping
        # its entry_id and UI-configured options stable across restarts
        if config_entry:
            if self.hass.config_entries.async_update_entry(
                config_entry,
                title=self._title(user_input),
                data=user_input,
            ):
                self.hass.config_entries.async_schedule_reload(
                    config_entry.entry_id
                )
            return self.async_abort(reason="already_configured")

        return self.async_create_entry(
            title=self._title(user_input),
            data=user_input,
        )

    async def async_step_user(self, user_input=None):
        """Create a new entity from UI."""

        if user_input is not None:
            await self.async_set_unique_id(self._unique_id(user_input))
            self._abort_if_unique_id_configured()

            if CONF_FLOW_PIN_NAME not in user_input:
                user_input[CONF_FLOW_PIN_NAME] = "pin %d:0x%02x:%d" % (
                    user_input[CONF_I2C_BUS],
                    user_input[CONF_I2C_ADDRESS],
                    user_input[CONF_FLOW_PIN_NUMBER],
                )

            if i2c_device_exist(user_input[CONF_I2C_BUS], user_input[CONF_I2C_ADDRESS]):
                return self.async_create_entry(
                    title=self._title(user_input),
                    data=user_input,
                )
            else:
                return self.async_abort(reason="invalid_i2c_address")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_I2C_BUS, default=DEFAULT_I2C_BUS
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=9)),
                    vol.Required(
                        CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=127)),
                    vol.Required(CONF_FLOW_PIN_NUMBER, default=0): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=15)
                    ),
                    vol.Required(
                        CONF_FLOW_PLATFORM,
                        default=PLATFORMS[0],
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=PLATFORMS,
                            mode=SelectSelectorMode.LIST,
                            translation_key="platform_type",
                        )
                    ),
                    vol.Optional(CONF_FLOW_PIN_NAME): str,
                }
            ),
        )


class Mcp23017OptionsFlowHandler(config_entries.OptionsFlow):
    """MCP23017 config flow options."""

    async def async_step_init(self, user_input=None):
        """Manage entity options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_INVERT_LOGIC,
                    default=self.config_entry.options.get(
                        CONF_INVERT_LOGIC, DEFAULT_INVERT_LOGIC
                    ),
                ): bool,
            }
        )
        if self.config_entry.data[CONF_FLOW_PLATFORM] == "binary_sensor":
            data_schema = data_schema.extend(
                {
                    vol.Optional(
                        CONF_PULL_MODE,
                        default=self.config_entry.options.get(
                            CONF_PULL_MODE, DEFAULT_PULL_MODE
                        ),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[PULL_MODE_UP, PULL_MODE_NONE],
                            mode=SelectSelectorMode.LIST,
                            translation_key="pull_mode",
                        )
                    ),
                }
            )

        if self.config_entry.data[CONF_FLOW_PLATFORM] in ("switch", "light"):
            data_schema = data_schema.extend(
                {
                    vol.Optional(
                        CONF_HW_SYNC,
                        default=self.config_entry.options.get(
                            CONF_HW_SYNC, DEFAULT_HW_SYNC
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_MOMENTARY,
                        default=self.config_entry.options.get(
                            CONF_MOMENTARY, DEFAULT_MOMENTARY
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_PULSE_TIME,
                        default=self.config_entry.options.get(
                            CONF_PULSE_TIME, DEFAULT_PULSE_TIME
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_PULSE_TIME, max=MAX_PULSE_TIME),
                    ),
                    vol.Optional(
                        CONF_SENSOR,
                        description={
                            "suggested_value": self.config_entry.options.get(
                                CONF_SENSOR
                            )
                        },
                    ): EntitySelector(
                        EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Optional(
                        CONF_DOUBLE_CLICK,
                        default=self.config_entry.options.get(
                            CONF_DOUBLE_CLICK, DEFAULT_DOUBLE_CLICK
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_DOUBLE_CLICK_WINDOW,
                        default=self.config_entry.options.get(
                            CONF_DOUBLE_CLICK_WINDOW, DEFAULT_DOUBLE_CLICK_WINDOW
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=100, max=5000)),
                    vol.Optional(
                        CONF_EVENT_SUPPRESS_MARGIN,
                        default=self.config_entry.options.get(
                            CONF_EVENT_SUPPRESS_MARGIN,
                            DEFAULT_EVENT_SUPPRESS_MARGIN,
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=100, max=10000)),
                }
            )
        return self.async_show_form(step_id="init", data_schema=data_schema)
