"""Constants for the Generic Fan Coil Thermostat integration."""

DOMAIN = "generic_fan_coil_thermostat"
PLATFORMS = ["climate"]

# Configuration options
CONF_CURRENT_TEMPERATURE_ENTITY_ID = "current_temperature_entity_id"
CONF_FAN_ENTITY_ID = "fan_entity_id"
CONF_COOLING_SWITCHES = "cooling_switches"
CONF_HEATING_SWITCHES = "heating_switches"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_TARGET_TEMP = "target_temp"
CONF_TEMP_STEP = "temp_step"

# Default settings
DEFAULT_MIN_TEMP = 15.0
DEFAULT_MAX_TEMP = 30.0
DEFAULT_TARGET_TEMP = 22.0
DEFAULT_TEMP_STEP = 0.5

# Fan modes
FAN_OFF = "off"
FAN_LOW = "low"
FAN_MED = "medium"
FAN_HIGH = "high"

# Threshold for fan speed
THRESHOLD_LOW = 0.5  # Temperature difference for activating low speed
THRESHOLD_MEDIUM = 1.5  # Temperature difference for activating medium speed
THRESHOLD_HIGH = 2.5  # Temperature difference for activating high speed
