# Generic Fan Coil Thermostat

A Home Assistant integration that turns any fan coil unit into a smart thermostat. It automatically manages fan speed and heating/cooling switches based on your room temperature and target setpoint.

## What Does It Do?
- Creates a climate entity in Home Assistant for your fan coil unit
- Automatically adjusts fan speed (off, low, medium, high) based on how far the room temperature is from your target
- Controls switches for heating and/or cooling (e.g., pumps, heat exchangers, boilers, chillers)
- Supports both automatic and manual fan speed control
- Works with any fan entity that supports preset modes
- Lets you set temperature, mode (heat/cool/off), and fan speed from the UI
- Integrates seamlessly with dashboards and automations

## How It Works
- When the room is too hot or cold, the integration turns on the appropriate switches and sets the fan speed higher as the temperature difference increases
- When the room reaches the target temperature, switches and fan turn off
- You can override fan speed manually, or let it run in "auto" mode
- Only the modes (heat/cool) for which you configure switches will be shown

## Example Use Cases
- Control a water-based fan coil unit with Home Assistant
- Automate heating/cooling pumps, heat exchangers, or electric heaters
- Use with underfloor heating or chilled beams
- Integrate with any fan that supports preset speeds

## Installation & Configuration
1. Copy the `custom_components/generic_fan_coil_thermostat` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Configure via UI or YAML:
   - Select your temperature sensor
   - Select your fan entity
   - Optionally add heating/cooling switches
   - Set temperature limits and step size

## Fan Speed Logic
- The farther the room temperature is from your target, the higher the fan speed
- Switches for heating/cooling are activated only when needed

## HACS Support
This repository is compatible with [HACS](https://hacs.xyz/). Add it as a custom repository for easy updates.

## Documentation & Support
See [GitHub documentation](https://github.com/recallfx/ha-generic-fan-coil-thermostat) and [issues](https://github.com/recallfx/ha-generic-fan-coil-thermostat/issues).
