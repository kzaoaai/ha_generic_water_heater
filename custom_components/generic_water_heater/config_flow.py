"""Config flow for Generic Water Heater integration."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector

from . import DOMAIN, CONF_HEATER, CONF_SENSOR, CONF_TARGET_TEMP, CONF_TEMP_DELTA, CONF_TEMP_MIN, CONF_TEMP_MAX, CONF_COOLDOWN


class GenericWaterHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Generic Water Heater."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return options flow handler for the config entry (compat helper)."""
        return OptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Create the config entry
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_HEATER): selector({"entity": {"domain": ["switch", "input_boolean"]}}),
                vol.Required(CONF_SENSOR): selector({"entity": {"domain": "sensor", "device_class": "temperature"}}),
                vol.Optional(CONF_TARGET_TEMP, default=45.0): vol.Coerce(float),
                vol.Optional(CONF_TEMP_DELTA, default=5.0): vol.Coerce(float),
                vol.Optional(CONF_TEMP_MIN): vol.Coerce(float),
                vol.Optional(CONF_TEMP_MAX): vol.Coerce(float),
                vol.Optional(CONF_COOLDOWN, default=10.0): vol.Coerce(float),
                vol.Optional("log_level", default="DEBUG"): selector(
                    {
                        "select": {
                            "options": [
                                {"value": "DEBUG", "label": "Debug"},
                                {"value": "INFO", "label": "Info"},
                                {"value": "WARNING", "label": "Warning"},
                            ]
                        }
                    }
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Generic Water Heater."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=current.get(CONF_NAME)): cv.string,
                vol.Required(CONF_HEATER, default=current.get(CONF_HEATER)): selector({"entity": {"domain": ["switch", "input_boolean"]}}),
                vol.Required(CONF_SENSOR, default=current.get(CONF_SENSOR)): selector({"entity": {"domain": "sensor", "device_class": "temperature"}}),
                vol.Optional(CONF_TARGET_TEMP, default=current.get(CONF_TARGET_TEMP, 45.0)): vol.Coerce(float),
                vol.Optional(CONF_TEMP_DELTA, default=current.get(CONF_TEMP_DELTA, 5.0)): vol.Coerce(float),
                vol.Optional(CONF_TEMP_MIN, default=current.get(CONF_TEMP_MIN)): vol.Coerce(float),
                vol.Optional(CONF_TEMP_MAX, default=current.get(CONF_TEMP_MAX)): vol.Coerce(float),
                vol.Optional(CONF_COOLDOWN, default=current.get(CONF_COOLDOWN, 10.0)): vol.Coerce(float),
                vol.Optional("log_level", default=current.get("log_level", "DEBUG")): selector(
                    {
                        "select": {
                            "options": [
                                {"value": "DEBUG", "label": "Debug"},
                                {"value": "INFO", "label": "Info"},
                                {"value": "WARNING", "label": "Warning"},
                            ]
                        }
                    }
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
