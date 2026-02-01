# Home Assistant Custom Component - Generic Water Heater

The `Generic Water Heater` integration is a custom component for Home Assistant that creates a virtual water heater entity. It controls a switch (connected to a heating element or boiler) based on a temperature sensor reading, effectively acting as a thermostat for your domestic hot water (DHW).

## Features

*   **Thermostat Logic**: Keeps water temperature within a specific range using a configurable hysteresis (delta).
*   **UI Configuration**: Fully supports Home Assistant's UI configuration flow and options.
*   **Manual Override**: Detects if the underlying switch is manually toggled and temporarily respects that state before resuming automatic control.
*   **Safety Cooldown**: Prevents rapid switching to protect electrical components (configurable, default 10s).
*   **Failsafe**: Automatically turns off the heater if the temperature sensor becomes unavailable.
*   **Device Linking**: Automatically attaches the water heater entity to the same device as the switch (if applicable).
*   **HVAC Action**: Reports current status as "Heating", "Idle" (Target reached), or "Off".

## Logic

The integration uses a hysteresis logic to prevent short-cycling:
*   **Turn ON**: When `Current Temperature` <= `Target Temperature` - `Delta`.
*   **Turn OFF**: When `Current Temperature` >= `Target Temperature`.

*Example*: Target 50°C, Delta 5°C.
The heater turns **ON** at 45°C and turns **OFF** at 50°C.

## Installation

### HACS (Recommended)
1.  Open HACS in Home Assistant.
2.  Add this repository as a Custom Repository (Integration).
3.  Search for "Generic Water Heater" and install.
4.  Restart Home Assistant.

### Manual
1.  Download the `custom_components/generic_water_heater` folder.
2.  Place it in your Home Assistant `config/custom_components/` directory.
3.  Restart Home Assistant.

## Configuration

### UI Configuration (Recommended)
1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for **Generic Water Heater**.
4.  Follow the setup wizard to select your switch, sensor, and parameters.

### YAML Configuration
Add the following to your `configuration.yaml`:

```yaml
generic_water_heater:
  bath_water:
    heater_switch: switch.dhw_switch
    temperature_sensor: sensor.dhw_temperature
    target_temperature: 50
    delta_temperature: 5
    min_temp: 30
    max_temp: 70
    cooldown: 10
```

### Configuration Options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `heater_switch` | entity_id | **Required** | The switch entity that controls the heater. |
| `temperature_sensor` | entity_id | **Required** | The sensor entity that reports water temperature. |
| `target_temperature` | float | 45.0 | Initial target temperature. |
| `delta_temperature` | float | 5.0 | The hysteresis buffer. Heater turns on at `Target - Delta`. |
| `min_temp` | float | *HA Default* | Minimum selectable temperature in the UI. |
| `max_temp` | float | *HA Default* | Maximum selectable temperature in the UI. |
| `cooldown` | float | 10.0 | Minimum time (seconds) between switch toggles to prevent rapid cycling. |
| `log_level` | string | DEBUG | Logging level (DEBUG, INFO, WARNING). |