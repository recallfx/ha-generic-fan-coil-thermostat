"""Config flow for Generic Fan Coil Thermostat integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_CURRENT_TEMPERATURE_ENTITY_ID,
    CONF_FAN_ENTITY_ID,
    CONF_COOLING_SWITCHES,
    CONF_HEATING_SWITCHES,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_TARGET_TEMP,
    CONF_TEMP_STEP,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_TARGET_TEMP,
    DEFAULT_TEMP_STEP,
)

_LOGGER = logging.getLogger(__name__)


class GenericFanCoilConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Generic Fan Coil Thermostat."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the entities exist
            hass = self.hass
            
            # Check if entities exist
            current_temp_entity = hass.states.get(user_input[CONF_CURRENT_TEMPERATURE_ENTITY_ID])
            fan_entity = hass.states.get(user_input[CONF_FAN_ENTITY_ID])
            
            if not current_temp_entity:
                errors[CONF_CURRENT_TEMPERATURE_ENTITY_ID] = "entity_not_found"
            if not fan_entity:
                errors[CONF_FAN_ENTITY_ID] = "entity_not_found"
                
            if not errors:
                # Check if this configuration already exists
                await self.async_set_unique_id(f"{user_input[CONF_CURRENT_TEMPERATURE_ENTITY_ID]}_{user_input[CONF_FAN_ENTITY_ID]}")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f"Generic Fan Coil Thermostat - {user_input[CONF_FAN_ENTITY_ID]}",
                    data=user_input
                )

        # Provide a form for the user to fill out
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CURRENT_TEMPERATURE_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["sensor", "climate"]),
                    ),
                    vol.Required(CONF_FAN_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["fan"]),
                    ),
                    vol.Optional(CONF_COOLING_SWITCHES, default=[]): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["switch"],
                            multiple=True,
                        ),
                    ),
                    vol.Optional(CONF_HEATING_SWITCHES, default=[]): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["switch"],
                            multiple=True,
                        ),
                    ),
                    vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
                    vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
                    vol.Optional(CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP): vol.Coerce(float),
                    vol.Optional(CONF_TEMP_STEP, default=DEFAULT_TEMP_STEP): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return GenericFanCoilOptionsFlowHandler(config_entry)


class GenericFanCoilOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the component."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(CONF_COOLING_SWITCHES, 
                default=self.config_entry.options.get(
                    CONF_COOLING_SWITCHES, self.config_entry.data.get(CONF_COOLING_SWITCHES, [])
                )
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["switch"],
                    multiple=True,
                ),
            ),
            vol.Optional(CONF_HEATING_SWITCHES, 
                default=self.config_entry.options.get(
                    CONF_HEATING_SWITCHES, self.config_entry.data.get(CONF_HEATING_SWITCHES, [])
                )
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["switch"],
                    multiple=True,
                ),
            ),
            vol.Optional(
                CONF_MIN_TEMP,
                default=self.config_entry.options.get(
                    CONF_MIN_TEMP, self.config_entry.data.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_MAX_TEMP,
                default=self.config_entry.options.get(
                    CONF_MAX_TEMP, self.config_entry.data.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_TARGET_TEMP,
                default=self.config_entry.options.get(
                    CONF_TARGET_TEMP, self.config_entry.data.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_TEMP_STEP,
                default=self.config_entry.options.get(
                    CONF_TEMP_STEP, self.config_entry.data.get(CONF_TEMP_STEP, DEFAULT_TEMP_STEP)
                ),
            ): vol.Coerce(float),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
