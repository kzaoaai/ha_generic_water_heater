# Home Assistant Custom Component - Generic Water Heater

The `Generic Water Heater` integration creates a virtual water heater entity in Home Assistant. It controls a switch using a temperature sensor, so you can manage domestic hot water with water heater controls in the UI and in automations.

## Features

- Thermostat-style control with configurable cold and hot tolerances.
- Smart Eco policy controlled by a dedicated switch plus a template condition.
- Optional extra sensor that tracks the highest recorded temperature in the last 7 days, useful for legionella prevention workflows.
- Manual override handling when the underlying switch is toggled directly.
- Minimum on and off durations to avoid rapid switching.
- Failsafe shutdown when the temperature sensor becomes unavailable.
- Automatic device linking to the same device as the controlled switch when possible.

## Heating Logic

The integration uses hysteresis to avoid short-cycling:

- Heat turns on when the current temperature is less than or equal to `target_temperature - cold_tolerance`.
- Heat turns off when the current temperature is greater than or equal to `target_temperature + hot_tolerance`.

Example with target `50°C`, cold tolerance `0.5°C`, and hot tolerance `0.5°C`:

- Heater turns on at `49.5°C` or lower.
- Heater turns off at `50.5°C` or higher.

Operation behavior:

- `off`: heater stays off.
- `electric`: follows the threshold logic above.
- `performance` (Boost): prioritizes heating.
- Smart Eco ON: applies the template condition as a heating allow/block policy.

## Installation

1. Open HACS in Home Assistant.
2. Add this repository as a Custom Repository for Integrations.
3. Search for `Generic Water Heater` and install it.
4. Restart Home Assistant.

## Configuration

This integration is configured from the Home Assistant UI.

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration**.
3. Search for **Generic Water Heater**.
4. Select the heater switch, temperature sensor, and your preferred operating parameters.

## Configuration Options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `heater_switch` | entity_id | Required | The switch entity that controls the heater. |
| `temperature_sensor` | entity_id | Required | The sensor that reports the water temperature. |
| `target_temperature_step` | float | `1.0` | The step used by the target temperature control in the UI. |
| `cold_tolerance` | float | `0.0` | Difference below target temperature that allows heating to turn on. |
| `hot_tolerance` | float | `0.0` | Difference above target temperature that forces heating to turn off. |
| `min_temp` | float | `15.0` | Minimum selectable target temperature. |
| `max_temp` | float | `80.0` | Maximum selectable target temperature. |
| `min_on_duration` | duration | `0 seconds` | Minimum time the heater must stay on before it can be turned off. |
| `min_off_duration` | duration | `120 seconds` | Minimum time the heater must stay off before it can be turned on. |
| `eco_mode_template_condition` | template | empty | Boolean template used by Smart Eco. When Smart Eco is ON and this evaluates to false, heating is blocked. When Smart Eco is OFF, this template is ignored. |
| `enable_max_temp_history_sensor` | boolean | `false` | Adds a sensor to the same device that exposes the highest recorded temperature in the last 7 days (useful in anti-legionella monitoring workflows). |

## Smart Eco

Smart Eco is a policy layer, not an operation mode:

- Smart Eco OFF: heater follows base mode behavior only.
- Smart Eco ON: the template condition can block heating.

Examples:

```jinja
{{ is_state('binary_sensor.solar_surplus', 'on') }}
```

```jinja
{{ states('sensor.grid_price_level') in ['low', 'very_low'] }}
```

```jinja
{{ states('sensor.pv_generation_w') | float(0) > 3000 }}
```

```jinja
{{ is_state('input_boolean.allow_eco_heating', 'on') }}
```

If Smart Eco is ON and the template evaluates to false, heating is blocked even if the target would otherwise request heat.
