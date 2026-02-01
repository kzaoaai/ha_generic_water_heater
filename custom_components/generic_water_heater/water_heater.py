"""Support for generic water heater units."""
import logging

from homeassistant.components.water_heater import (
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_NAME,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import DOMAIN as HA_DOMAIN, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers import device_registry as dr, entity_registry as er

from homeassistant.const import UnitOfTemperature
from homeassistant.util.unit_conversion import TemperatureConverter

from . import DOMAIN, CONF_HEATER, CONF_SENSOR, CONF_TARGET_TEMP, CONF_TEMP_DELTA, CONF_TEMP_MIN, CONF_TEMP_MAX

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Generic Water Heater"


async def async_setup_platform(
    hass, hass_config, async_add_entities, discovery_info=None
):
    """Set up the generic water_heater devices."""
    entities = []

    for config in discovery_info:
        name = config[CONF_NAME]
        heater_entity_id = config[CONF_HEATER]
        sensor_entity_id = config[CONF_SENSOR]
        target_temp = config.get(CONF_TARGET_TEMP, 45.0)
        temp_delta = config.get(CONF_TEMP_DELTA, 5.0)
        min_temp = config.get(CONF_TEMP_MIN)
        max_temp = config.get(CONF_TEMP_MAX)
        log_level = config.get("log_level", "DEBUG")
        unit = hass.config.units.temperature_unit

        registry = er.async_get(hass)
        entity_entry = registry.async_get(heater_entity_id)
        device_identifiers = None
        if entity_entry and entity_entry.device_id:
            device_registry = dr.async_get(hass)
            device_entry = device_registry.async_get(entity_entry.device_id)
            if device_entry:
                device_identifiers = device_entry.identifiers

        entities.append(
            GenericWaterHeater(
                name,
                heater_entity_id,
                sensor_entity_id,
                target_temp,
                temp_delta,
                min_temp,
                max_temp,
                unit,
                log_level=log_level,
                config_entry_id=None,
                device_identifiers=device_identifiers,
            )
        )

    async_add_entities(entities)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a water heater from a config entry."""
    # merge entry data and options so options override data
    data = {**entry.data, **getattr(entry, "options", {})}
    name = data.get(CONF_NAME, DEFAULT_NAME)
    heater_entity_id = data.get(CONF_HEATER)
    sensor_entity_id = data.get(CONF_SENSOR)
    target_temp = data.get(CONF_TARGET_TEMP)
    temp_delta = data.get(CONF_TEMP_DELTA)
    min_temp = data.get(CONF_TEMP_MIN)
    max_temp = data.get(CONF_TEMP_MAX)
    unit = hass.config.units.temperature_unit
    log_level = data.get("log_level", "DEBUG")

    registry = er.async_get(hass)
    entity_entry = registry.async_get(heater_entity_id)
    device_identifiers = None
    if entity_entry and entity_entry.device_id:
        device_registry = dr.async_get(hass)
        device_entry = device_registry.async_get(entity_entry.device_id)
        if device_entry:
            device_identifiers = device_entry.identifiers

    async_add_entities(
        [
            GenericWaterHeater(
                name,
                heater_entity_id,
                sensor_entity_id,
                target_temp,
                temp_delta,
                min_temp,
                max_temp,
                unit,
                log_level=log_level,
                config_entry_id=entry.entry_id,
                device_identifiers=device_identifiers,
            )
        ]
    )
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry for this platform."""
    # Entities are removed automatically when the config entry is removed/unloaded
    return True


class GenericWaterHeater(WaterHeaterEntity, RestoreEntity):
    """Representation of a generic water_heater device."""

    def __init__(
        self,
        name,
        heater_entity_id,
        sensor_entity_id,
        target_temp,
        temp_delta,
        min_temp,
        max_temp,
        unit,
        log_level: str = "DEBUG",
        config_entry_id=None,
        device_identifiers=None,
    ):
        """Initialize the water_heater device."""
        self._attr_name = name
        self.heater_entity_id = heater_entity_id
        self.sensor_entity_id = sensor_entity_id
        self._attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.OPERATION_MODE
        self._target_temperature = target_temp
        self._temperature_delta = temp_delta
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._unit_of_measurement = unit
        self._current_operation = STATE_ON
        self._current_temperature = None
        self._operation_list = [
            STATE_ON,
            STATE_OFF,
        ]
        self._attr_available = False
        self._attr_should_poll = False
        self._log_level = log_level.upper() if log_level else "DEBUG"
        self._device_identifiers = device_identifiers
        # device/unique id
        # prefer config_entry_id (when created via UI) otherwise fall back to heater entity id
        self._device_identifier = config_entry_id or heater_entity_id
        # expose unique_id for the entity
        try:
            self._attr_unique_id = f"{DOMAIN}_{self._device_identifier}"
        except Exception:
            pass

    @property
    def device_info(self):
        """Return device information for the device registry."""
        if self._device_identifiers:
            return {
                "identifiers": self._device_identifiers,
            }
        return {
            "identifiers": {(DOMAIN, self._device_identifier)},
            "name": self._attr_name,
        }

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        return {
            "hvac_action": self.hvac_action
        }

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported."""
        if self._current_operation == STATE_OFF:
            return "off"
        heater = self.hass.states.get(self.heater_entity_id)
        if heater and heater.state == STATE_ON:
            return "heating"
        return "idle"

    def _maybe_log(self, msg, *args):
        """Log at debug or info depending on configured log level."""
        if self._log_level == "DEBUG":
            _LOGGER.debug(msg, *args)
        elif self._log_level == "INFO":
            _LOGGER.info(msg, *args)
        elif self._log_level == "WARNING":
            # skip debug/info messages at WARNING level
            return

    @property
    def current_temperature(self):
        """Return current temperature."""
        return self._current_temperature

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def current_operation(self):
        """Return current operation ie. on, off."""
        return self._current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def min_temp(self):
        """Return the minimum targetable temperature."""
        """If the min temperature is not set on the config, returns the HA default for Water Heaters."""
        if self._min_temp is None:
            return TemperatureConverter.convert(DEFAULT_MIN_TEMP, UnitOfTemperature.FAHRENHEIT, self._unit_of_measurement) 
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum targetable temperature."""
        """If the max temperature is not set on the config, returns the HA default for Water Heaters."""
        if self._max_temp is None:
            return TemperatureConverter.convert(DEFAULT_MAX_TEMP, UnitOfTemperature.FAHRENHEIT, self._unit_of_measurement) 
        return self._max_temp

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self._maybe_log("%s: async_set_temperature -> target=%s", self.name, self._target_temperature)
        await self._async_control_heating()

    async def async_set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        self._current_operation = operation_mode
        self._maybe_log("%s: async_set_operation_mode -> mode=%s", self.name, self._current_operation)
        await self._async_control_heating()

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.sensor_entity_id], self._async_sensor_changed
            )
        )
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.heater_entity_id], self._async_switch_changed
            )
        )

        old_state = await self.async_get_last_state()
        if old_state is not None:
            if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                self._target_temperature = float(old_state.attributes.get(ATTR_TEMPERATURE))
            self._current_operation = old_state.state

        temp_sensor = self.hass.states.get(self.sensor_entity_id)
        if temp_sensor and temp_sensor.state not in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            self._current_temperature = float(temp_sensor.state)

        heater_switch = self.hass.states.get(self.heater_entity_id)
        if heater_switch and heater_switch.state not in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            self._attr_available = True
        
        await self._async_control_heating()
        self.async_write_ha_state()

    async def _async_sensor_changed(self, event):
        """Handle temperature changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            # Failsafe
            _LOGGER.warning(
                "No Temperature information, entering Failsafe, turning off heater %s",
                self.heater_entity_id,
            )
            await self._async_heater_turn_off()
            self._current_temperature = None
        else:
            self._current_temperature = float(new_state.state)

        self._maybe_log(
            "%s: sensor changed -> current_temperature=%s, target=%s, delta=%s",
            self.name,
            self._current_temperature,
            self._target_temperature,
            self._temperature_delta,
        )

        await self._async_control_heating()

    @callback
    def _async_switch_changed(self, event):
        """Handle heater switch state changes."""
        new_state = event.data.get("new_state")
        self._maybe_log("New switch state = %s", new_state)
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._attr_available = False
        else:
            self._attr_available = True
            self._maybe_log("%s became Available", self.name)

        self.async_write_ha_state()

    async def _async_control_heating(self):
        """Check if we need to turn heating on or off."""
        self._maybe_log(
            "%s: control_heating start -> operation=%s, current_temperature=%s, target=%s, delta=%s",
            self.name,
            self._current_operation,
            self._current_temperature,
            self._target_temperature,
            self._temperature_delta,
        )

        # If the water heater mode is explicitly OFF, ensure underlying switch is off
        if self._current_operation == STATE_OFF:
            self._maybe_log("%s: operation is OFF, turning underlying switch off", self.name)
            await self._async_heater_turn_off()
            self.async_write_ha_state()
            return

        # If we don't have the required temperature information, just update state
        if (
            self._current_temperature is None
            or self._target_temperature is None
            or self._temperature_delta is None
        ):
            self._maybe_log("%s: missing temperature/target/delta, skipping control", self.name)
            self.async_write_ha_state()
            return

        # Control heating based on temperature delta
        # Logic: Turn ON if temp <= target - delta. Turn OFF if temp >= target.
        if self._current_temperature <= (self._target_temperature - self._temperature_delta):
            self._maybe_log("%s: current <= (target - delta) -> turning ON", self.name)
            await self._async_heater_turn_on()
        elif self._current_temperature >= self._target_temperature:
            self._maybe_log("%s: current >= target -> turning OFF", self.name)
            await self._async_heater_turn_off()
        # Else: stay in current state (hysteresis band)

        self.async_write_ha_state()

    async def _async_heater_turn_on(self):
        """Turn heater toggleable device on."""
        heater = self.hass.states.get(self.heater_entity_id)
        if heater is None or heater.state == STATE_ON:
            return

        self._maybe_log("Turning on heater %s", self.heater_entity_id)
        data = {ATTR_ENTITY_ID: self.heater_entity_id}
        await self.hass.services.async_call(
            HA_DOMAIN, SERVICE_TURN_ON, data, context=self._context
        )

    async def _async_heater_turn_off(self):
        """Turn heater toggleable device off."""
        heater = self.hass.states.get(self.heater_entity_id)
        if heater is None or heater.state == STATE_OFF:
            return

        self._maybe_log("Turning off heater %s", self.heater_entity_id)
        data = {ATTR_ENTITY_ID: self.heater_entity_id}
        await self.hass.services.async_call(
            HA_DOMAIN, SERVICE_TURN_OFF, data, context=self._context
        )
