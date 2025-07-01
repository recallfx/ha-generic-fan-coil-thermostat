# Generic Fan Coil Thermostat Component

This custom component creates a climate entity that behaves like a thermostat for controlling both heating and cooling with fan speed control. It automatically adjusts the fan speed based on the temperature difference between the current room temperature and the target temperature.

## Features

- Works as a standard Home Assistant climate entity
- Automatically controls fan speed based on temperature difference
- Controls additional switches when heating or cooling is needed (e.g., heat exchangers, pumps, heating elements)
- Supports both automatic and manual fan speed control
- Supports heating, cooling, or both modes depending on configured switches
- Configurable through the UI
- Works with any fan entity that supports preset modes

## Installation

1. Place the `generic_fan_coil_thermostat` folder in your `custom_components` directory
2. Restart Home Assistant
3. Go to **Settings** > **Devices & Services** > **+ Add Integration**
4. Search for "Generic Fan Coil Thermostat" and add it
5. Follow the configuration wizard to set up your thermostat

## Configuration

During setup, you'll need to provide:

- Temperature sensor entity to use for monitoring room temperature
- Fan entity to control (must support preset modes: low, medium, high)
- Optional cooling switches (e.g., heat exchanger switches, pump controls) - these will be turned on when cooling is active
- Optional heating switches (e.g., heating elements, boiler controls) - these will be turned on when heating is active
- Optional temperature settings (min, max, default target, step size)

**Note:** The thermostat will only show heating and/or cooling modes if the corresponding switches are configured. If no switches are configured, both heating and cooling modes will be available for fan-only operation.

## Usage

Once installed, the Generic Fan Coil Thermostat will appear as a climate entity that you can add to your dashboards using any of the standard climate cards.

- Set the target temperature like any other thermostat
- Switch between "Off", "Heat", and "Cool" modes (available modes depend on configured switches)
- Select fan mode: auto, off, low, medium, or high
  - In "auto" mode, the fan speed is controlled automatically based on temperature difference
  - In manual modes (off, low, medium, high), the fan stays at the selected speed regardless of temperature
  - When thermostat mode is "Off", switches are turned off but fan remains in its current state if manually controlled
- Heating and cooling switches are controlled automatically based on demand, regardless of fan mode

## Fan Speed Control Logic

### Cooling Mode
- Temperature difference < 0.5°C: Fan OFF, Cooling switches OFF
- Temperature difference 0.5-1.5°C: Fan LOW, Cooling switches ON
- Temperature difference 1.5-2.5°C: Fan MEDIUM, Cooling switches ON
- Temperature difference > 2.5°C: Fan HIGH, Cooling switches ON

### Heating Mode
- Temperature difference < -0.5°C: Fan OFF, Heating switches OFF
- Temperature difference -0.5°C to -1.5°C: Fan LOW, Heating switches ON
- Temperature difference -1.5°C to -2.5°C: Fan MEDIUM, Heating switches ON
- Temperature difference < -2.5°C: Fan HIGH, Heating switches ON

*Temperature difference = Current Temperature - Target Temperature*

## Example Use Cases

### For Cooling Switches
- Heat exchanger controls for water cooling systems
- Water pumps for cooling circuits
- Valve actuators for cooling water flow
- Additional cooling equipment like chillers
- Any switch that needs to be active during cooling operation

### For Heating Switches
- Heating elements or electric heaters
- Boiler or heating system controls
- Water pumps for heating circuits
- Valve actuators for heating water flow
- Underfloor heating controls
- Any switch that needs to be active during heating operation
