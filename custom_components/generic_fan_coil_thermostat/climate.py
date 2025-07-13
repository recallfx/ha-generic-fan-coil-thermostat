"""Climate platform for Generic Fan Coil Thermostat integration."""
import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_CURRENT_TEMPERATURE_ENTITY_ID,
    CONF_FAN_ENTITY_ID,
    CONF_COOLING_SWITCHES,
    CONF_HEATING_SWITCHES,
    CONF_MAX_TEMP,
    CONF_MIN_TEMP,
    CONF_TARGET_TEMP,
    CONF_TEMP_STEP,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DEFAULT_TARGET_TEMP,
    DEFAULT_TEMP_STEP,
    DOMAIN,
    FAN_HIGH,
    FAN_LOW,
    FAN_OFF,
    FAN_MED,
    THRESHOLD_HIGH,
    THRESHOLD_LOW,
    THRESHOLD_MEDIUM,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Generic Fan Coil Thermostat climate platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities(
        [
            GenericFanCoilThermostat(
                hass,
                config_entry.entry_id,
                data.get(CONF_CURRENT_TEMPERATURE_ENTITY_ID),
                data.get(CONF_FAN_ENTITY_ID),
                data.get(CONF_COOLING_SWITCHES, []),
                data.get(CONF_HEATING_SWITCHES, []),
                data.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP),
                data.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP),
                data.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP),
                data.get(CONF_TEMP_STEP, DEFAULT_TEMP_STEP),
            )
        ]
    )


class GenericFanCoilThermostat(ClimateEntity, RestoreEntity):
    """Representation of a Generic Fan Coil Thermostat."""

    _attr_has_entity_name = True
    _attr_name = "Generic Fan Coil Thermostat"
    _attr_icon = "mdi:thermostat"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
    )
    _enable_turn_on_off_backwards_compatibility = False
    _attr_fan_modes = ["off", "low", "medium", "high", "auto"]

    def __init__(
        self,
        hass,
        unique_id,
        current_temp_entity_id,
        fan_entity_id,
        cooling_switches,
        heating_switches,
        min_temp,
        max_temp,
        target_temp,
        temp_step,
    ):
        """Initialize the thermostat."""
        self.hass = hass
        self._attr_unique_id = unique_id
        self._current_temp_entity_id = current_temp_entity_id
        self._fan_entity_id = fan_entity_id
        self._cooling_switches = cooling_switches or []
        self._heating_switches = heating_switches or []
        
        # Determine available HVAC modes based on configured switches
        hvac_modes = [HVACMode.OFF]
        if self._cooling_switches:
            hvac_modes.append(HVACMode.COOL)
        if self._heating_switches:
            hvac_modes.append(HVACMode.HEAT)
        # If no switches configured, still allow both modes (fan-only operation)
        if not self._cooling_switches and not self._heating_switches:
            hvac_modes.extend([HVACMode.HEAT, HVACMode.COOL])
        self._attr_hvac_modes = hvac_modes
        
        _LOGGER.debug(f"Initializing thermostat with cooling switches: {self._cooling_switches}")
        _LOGGER.debug(f"Initializing thermostat with heating switches: {self._heating_switches}")
        _LOGGER.debug(f"Available HVAC modes: {hvac_modes}")
        
        self._attr_min_temp = min_temp
        self._attr_max_temp = max_temp
        self._attr_target_temperature = target_temp
        self._attr_target_temperature_step = temp_step
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_current_temperature = None
        self._attr_fan_mode = "auto"
        self._attr_hvac_action = HVACAction.OFF
        self._current_fan_mode = FAN_OFF

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Restore previous state if available
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_hvac_mode = last_state.state
            if last_state.attributes.get(ATTR_TEMPERATURE) is not None:
                self._attr_target_temperature = last_state.attributes.get(ATTR_TEMPERATURE)
            if last_state.attributes.get("fan_mode") is not None:
                self._attr_fan_mode = last_state.attributes.get("fan_mode")

        # Add listeners
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._current_temp_entity_id], self._async_temp_changed
            )
        )

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._fan_entity_id], self._async_fan_changed
            )
        )

        # Get initial temperature
        current_temp_state = self.hass.states.get(self._current_temp_entity_id)
        if current_temp_state and current_temp_state.state not in (
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            self._attr_current_temperature = float(current_temp_state.state)

        # Run control logic on startup
        self.async_control_fan()

    @callback
    def _async_temp_changed(self, event):
        """Handle temperature changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return

        try:
            self._attr_current_temperature = float(new_state.state)
            self.async_control_fan()
            self.async_write_ha_state()
        except ValueError as ex:
            _LOGGER.error("Unable to update from temperature sensor: %s", ex)

    @callback
    def _async_fan_changed(self, event):
        """Handle fan state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        # Update our internal state to match the fan state
        if new_state.state == STATE_OFF:
            self._current_fan_mode = FAN_OFF
        else:
            # Get the current fan mode from the fan entity
            preset_mode = new_state.attributes.get("preset_mode", FAN_LOW)
            self._current_fan_mode = preset_mode

        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]
            self.async_control_fan()
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode."""
        if fan_mode not in self.fan_modes:
            raise ValueError(f"Invalid fan mode: {fan_mode}")
        
        self._attr_fan_mode = fan_mode
        
        # If we're in automatic mode, let the control logic handle it
        if fan_mode == "auto":
            self.async_control_fan()
        else:
            # Otherwise directly set the fan mode
            await self.async_update_fan(fan_mode)
            
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        if hvac_mode not in self.hvac_modes:
            raise ValueError(f"Invalid hvac mode: {hvac_mode}")
            
        self._attr_hvac_mode = hvac_mode
        
        if hvac_mode == HVACMode.OFF:
            # Turn off all switches but only turn off fan if it's in auto mode
            await self.async_turn_off_cooling_switches()
            await self.async_turn_off_heating_switches()
            if self._attr_fan_mode == "auto":
                await self.hass.services.async_call(
                    "fan", "turn_off", {"entity_id": self._fan_entity_id}
                )
            self._attr_hvac_action = HVACAction.OFF
        else:
            # Run control logic
            self.async_control_fan()
        
        self.async_write_ha_state()

    def async_control_fan(self):
        """Control the fan based on temperature difference."""
        if self._attr_hvac_mode == HVACMode.OFF:
            _LOGGER.debug("HVAC mode is OFF, skipping fan control")
            return
            
        if self._attr_current_temperature is None or self._attr_target_temperature is None:
            _LOGGER.debug("Temperature values not available, skipping fan control")
            return

        # Calculate temperature difference
        temp_diff = self._attr_current_temperature - self._attr_target_temperature
        _LOGGER.debug(f"Temperature difference: {temp_diff}°C (current: {self._attr_current_temperature}°C, target: {self._attr_target_temperature}°C)")

        if self._attr_hvac_mode == HVACMode.COOL:
            self._control_cooling(temp_diff)
        elif self._attr_hvac_mode == HVACMode.HEAT:
            self._control_heating(temp_diff)

    def _control_cooling(self, temp_diff):
        """Control cooling based on temperature difference."""
        # Determine the desired fan state based on temperature difference
        if temp_diff < THRESHOLD_LOW:
            # Temperature below threshold, turn off cooling switches and fan (if auto)
            _LOGGER.debug(f"Temperature difference {temp_diff}°C < {THRESHOLD_LOW}°C, turning off cooling")
            self._attr_hvac_action = HVACAction.IDLE
            if self._attr_fan_mode == "auto":
                self.hass.async_create_task(self.async_update_fan(FAN_OFF))
            self.hass.async_create_task(self.async_turn_off_cooling_switches())
        elif temp_diff < THRESHOLD_MEDIUM:
            # Small difference, use low speed and turn on cooling switches
            _LOGGER.debug(f"Temperature difference {temp_diff}°C, using LOW fan speed for cooling")
            self._attr_hvac_action = HVACAction.COOLING
            if self._attr_fan_mode == "auto":
                self.hass.async_create_task(self.async_update_fan(FAN_LOW))
            self.hass.async_create_task(self.async_turn_on_cooling_switches())
        elif temp_diff < THRESHOLD_HIGH:
            # Medium difference, use medium speed and turn on cooling switches
            _LOGGER.debug(f"Temperature difference {temp_diff}°C, using MEDIUM fan speed for cooling")
            self._attr_hvac_action = HVACAction.COOLING
            if self._attr_fan_mode == "auto":
                self.hass.async_create_task(self.async_update_fan(FAN_MED))
            self.hass.async_create_task(self.async_turn_on_cooling_switches())
        else:
            # Large difference, use high speed and turn on cooling switches
            _LOGGER.debug(f"Temperature difference {temp_diff}°C, using HIGH fan speed for cooling")
            self._attr_hvac_action = HVACAction.COOLING
            if self._attr_fan_mode == "auto":
                self.hass.async_create_task(self.async_update_fan(FAN_HIGH))
            self.hass.async_create_task(self.async_turn_on_cooling_switches())

    def _control_heating(self, temp_diff):
        """Control heating based on temperature difference."""
        # For heating, we need negative temperature difference (current < target)
        heating_diff = -temp_diff  # Convert to positive value for heating need
        
        if heating_diff < THRESHOLD_LOW:
            # Temperature above threshold, turn off heating switches and fan (if auto)
            _LOGGER.debug(f"Heating difference {heating_diff}°C < {THRESHOLD_LOW}°C, turning off heating")
            self._attr_hvac_action = HVACAction.IDLE
            if self._attr_fan_mode == "auto":
                self.hass.async_create_task(self.async_update_fan(FAN_OFF))
            self.hass.async_create_task(self.async_turn_off_heating_switches())
        elif heating_diff < THRESHOLD_MEDIUM:
            # Small difference, use low speed and turn on heating switches
            _LOGGER.debug(f"Heating difference {heating_diff}°C, using LOW fan speed for heating")
            self._attr_hvac_action = HVACAction.HEATING
            if self._attr_fan_mode == "auto":
                self.hass.async_create_task(self.async_update_fan(FAN_LOW))
            self.hass.async_create_task(self.async_turn_on_heating_switches())
        elif heating_diff < THRESHOLD_HIGH:
            # Medium difference, use medium speed and turn on heating switches
            _LOGGER.debug(f"Heating difference {heating_diff}°C, using MEDIUM fan speed for heating")
            self._attr_hvac_action = HVACAction.HEATING
            if self._attr_fan_mode == "auto":
                self.hass.async_create_task(self.async_update_fan(FAN_MED))
            self.hass.async_create_task(self.async_turn_on_heating_switches())
        else:
            # Large difference, use high speed and turn on heating switches
            _LOGGER.debug(f"Heating difference {heating_diff}°C, using HIGH fan speed for heating")
            self._attr_hvac_action = HVACAction.HEATING
            if self._attr_fan_mode == "auto":
                self.hass.async_create_task(self.async_update_fan(FAN_HIGH))
            self.hass.async_create_task(self.async_turn_on_heating_switches())

    async def async_update_fan(self, mode):
        """Update the fan state."""
        if mode == FAN_OFF:
            await self.hass.services.async_call(
                "fan", "turn_off", {"entity_id": self._fan_entity_id}
            )
        else:
            # Turn on fan and set its mode
            await self.hass.services.async_call(
                "fan", "turn_on", {"entity_id": self._fan_entity_id}
            )
            
            await self.hass.services.async_call(
                "fan", 
                "set_preset_mode", 
                {
                    "entity_id": self._fan_entity_id,
                    "preset_mode": mode
                }
            )

    async def async_turn_on_cooling_switches(self):
        """Turn on all cooling switches."""
        if not self._cooling_switches:
            _LOGGER.debug("No cooling switches configured")
            return
            
        _LOGGER.debug(f"Turning ON cooling switches: {self._cooling_switches}")
        
        # Turn on all switches in a single service call if possible
        try:
            await self.hass.services.async_call(
                "switch", 
                "turn_on", 
                {"entity_id": self._cooling_switches}
            )
            _LOGGER.debug("Successfully turned ON all cooling switches")
        except Exception as ex:
            _LOGGER.error(f"Error turning on cooling switches: {ex}")
            # Fallback to individual calls
            for switch_entity in self._cooling_switches:
                try:
                    _LOGGER.debug(f"Turning ON switch individually: {switch_entity}")
                    await self.hass.services.async_call(
                        "switch", "turn_on", {"entity_id": switch_entity}
                    )
                except Exception as switch_ex:
                    _LOGGER.error(f"Error turning on switch {switch_entity}: {switch_ex}")

    async def async_turn_off_cooling_switches(self):
        """Turn off all cooling switches."""
        if not self._cooling_switches:
            _LOGGER.debug("No cooling switches configured")
            return
            
        _LOGGER.debug(f"Turning OFF cooling switches: {self._cooling_switches}")
        
        # Turn off all switches in a single service call if possible
        try:
            await self.hass.services.async_call(
                "switch", 
                "turn_off", 
                {"entity_id": self._cooling_switches}
            )
            _LOGGER.debug("Successfully turned OFF all cooling switches")
        except Exception as ex:
            _LOGGER.error(f"Error turning off cooling switches: {ex}")
            # Fallback to individual calls
            for switch_entity in self._cooling_switches:
                try:
                    _LOGGER.debug(f"Turning OFF switch individually: {switch_entity}")
                    await self.hass.services.async_call(
                        "switch", "turn_off", {"entity_id": switch_entity}
                    )
                except Exception as switch_ex:
                    _LOGGER.error(f"Error turning off switch {switch_entity}: {switch_ex}")

    async def async_turn_on_heating_switches(self):
        """Turn on all heating switches."""
        if not self._heating_switches:
            _LOGGER.debug("No heating switches configured")
            return
            
        _LOGGER.debug(f"Turning ON heating switches: {self._heating_switches}")
        
        # Turn on all switches in a single service call if possible
        try:
            await self.hass.services.async_call(
                "switch", 
                "turn_on", 
                {"entity_id": self._heating_switches}
            )
            _LOGGER.debug("Successfully turned ON all heating switches")
        except Exception as ex:
            _LOGGER.error(f"Error turning on heating switches: {ex}")
            # Fallback to individual calls
            for switch_entity in self._heating_switches:
                try:
                    _LOGGER.debug(f"Turning ON heating switch individually: {switch_entity}")
                    await self.hass.services.async_call(
                        "switch", "turn_on", {"entity_id": switch_entity}
                    )
                except Exception as switch_ex:
                    _LOGGER.error(f"Error turning on heating switch {switch_entity}: {switch_ex}")

    async def async_turn_off_heating_switches(self):
        """Turn off all heating switches."""
        if not self._heating_switches:
            _LOGGER.debug("No heating switches configured")
            return
            
        _LOGGER.debug(f"Turning OFF heating switches: {self._heating_switches}")
        
        # Turn off all switches in a single service call if possible
        try:
            await self.hass.services.async_call(
                "switch", 
                "turn_off", 
                {"entity_id": self._heating_switches}
            )
            _LOGGER.debug("Successfully turned OFF all heating switches")
        except Exception as ex:
            _LOGGER.error(f"Error turning off heating switches: {ex}")
            # Fallback to individual calls
            for switch_entity in self._heating_switches:
                try:
                    _LOGGER.debug(f"Turning OFF heating switch individually: {switch_entity}")
                    await self.hass.services.async_call(
                        "switch", "turn_off", {"entity_id": switch_entity}
                    )
                except Exception as switch_ex:
                    _LOGGER.error(f"Error turning off heating switch {switch_entity}: {switch_ex}")
