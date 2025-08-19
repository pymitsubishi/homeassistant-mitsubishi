"""Climate platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    FAN_AUTO,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pymitsubishi import (
    DriveMode,
    HorizontalWindDirection,
    PowerOnOff,
    VerticalWindDirection,
    WindSpeed,
)

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity
from .select import (
    HORIZONTAL_WIND_OPTIONS,
    HORIZONTAL_WIND_REVERSE,
    VERTICAL_WIND_OPTIONS,
    VERTICAL_WIND_REVERSE,
)

_LOGGER = logging.getLogger(__name__)

# Mapping from HA HVAC modes to Mitsubishi modes
HVAC_MODE_MAP = {
    HVACMode.OFF: PowerOnOff.OFF,
    HVACMode.HEAT: DriveMode.HEATER,
    HVACMode.COOL: DriveMode.COOLER,
    HVACMode.AUTO: DriveMode.AUTO,
    HVACMode.DRY: DriveMode.DEHUM,
    HVACMode.FAN_ONLY: DriveMode.FAN,
}

HVAC_MODE_REVERSE_LOOKUP = {v: k for k, v in HVAC_MODE_MAP.items()}

# Fan speed mapping
FAN_SPEED_MAP = {
    FAN_AUTO: WindSpeed.AUTO,
    "1": WindSpeed.LEVEL_1,
    "2": WindSpeed.LEVEL_2,
    "3": WindSpeed.LEVEL_3,
    "4": WindSpeed.LEVEL_4,
    "5": WindSpeed.LEVEL_FULL,
}

MITSUBISHI_TO_FAN_MODE =  {v: k for k, v in FAN_SPEED_MAP.items()}

# HVAC Action mapping
HVAC_ACTION_MAP = {
    DriveMode.HEATER: HVACAction.HEATING,
    DriveMode.COOLER: HVACAction.COOLING,
    DriveMode.AUTO: HVACAction.IDLE,
    DriveMode.AUTO_COOLER: HVACAction.COOLING,
    DriveMode.AUTO_HEATER: HVACAction.HEATING,
    DriveMode.DEHUM: HVACAction.DRYING,
    DriveMode.FAN: HVACAction.FAN,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi climate platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([MitsubishiClimate(coordinator, config_entry)])


class MitsubishiClimate(MitsubishiEntity, ClimateEntity):
    """Representation of a Mitsubishi air conditioner."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 16.0
    _attr_max_temp = 32.0
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_AUTO, "1", "2", "3", "4", "5"]
    _attr_swing_modes = list(VERTICAL_WIND_OPTIONS.keys())
    _attr_swing_horizontal_modes = list(HORIZONTAL_WIND_OPTIONS.keys())

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.SWING_HORIZONTAL_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, config_entry, "climate")
        self._config_entry = config_entry

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if room_temp := self.coordinator.data.get("room_temp"):
            return float(room_temp)
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if target_temp := self.coordinator.data.get("target_temp"):
            return float(target_temp)
        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self._execute_command_with_refresh(
            f"set temperature to {temperature}°C",
            self.coordinator.controller.set_temperature,
            temperature,
        )

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        power = self.coordinator.data.get("power")
        if power == "OFF":
            return HVACMode.OFF

        # Get the drive mode from coordinator data
        mode_name = self.coordinator.data.get("mode")
        if mode_name:
            try:
                drive_mode = DriveMode[mode_name]
                return HVAC_MODE_REVERSE_LOOKUP.get(drive_mode, HVACMode.OFF)
            except (KeyError, ValueError):
                return HVACMode.OFF

        return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self._execute_command_with_refresh(
                f"set HVAC mode to {hvac_mode}", self.coordinator.controller.set_power, False
            )
        else:
            # Turn on if currently off
            if self.hvac_mode == HVACMode.OFF:
                power_success = await self._execute_command_with_refresh(
                    "turn on device before setting mode",
                    self.coordinator.controller.set_power,
                    True,
                )
                if not power_success:
                    return

            # Set the mode
            if hvac_mode in HVAC_MODE_MAP:
                drive_mode = HVAC_MODE_MAP[hvac_mode]
                if isinstance(drive_mode, DriveMode):
                    await self._execute_command_with_refresh(
                        f"set HVAC mode to {hvac_mode}",
                        self.coordinator.controller.set_mode,
                        drive_mode,
                    )

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF

        # Check if we have energy state data to determine if compressor is running
        energy_states = self.coordinator.data.get("energy_states")
        if energy_states and "operating" in energy_states:
            is_operating = energy_states["operating"]

            # If compressor is not running, device is idle regardless of mode
            if not is_operating:
                return HVACAction.IDLE

        # If compressor is running or we don't have operating data,
        # determine action based on mode
        mode_name = self.coordinator.data.get("mode")
        if mode_name:
            try:
                drive_mode = DriveMode[mode_name]
                return HVAC_ACTION_MAP.get(drive_mode, HVACAction.IDLE)
            except (KeyError, ValueError):
                pass

        return HVACAction.IDLE

    @property
    def fan_mode(self) -> str:
        """Return the fan setting."""
        fan_speed_name = self.coordinator.data.get("fan_speed")
        if fan_speed_name:
            try:
                wind_speed = WindSpeed[fan_speed_name]
                return MITSUBISHI_TO_FAN_MODE.get(wind_speed, FAN_AUTO)
            except (KeyError, ValueError):
                pass
        return FAN_AUTO

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        if fan_mode in FAN_SPEED_MAP:
            wind_speed = FAN_SPEED_MAP[fan_mode]
            await self._execute_command_with_refresh(
                f"set fan mode to {fan_mode}", self.coordinator.controller.set_fan_speed, wind_speed
            )

    @property
    def swing_mode(self) -> str:
        """Return the swing setting."""
        mitsubishi_swing_mode = VerticalWindDirection[self.coordinator.data.get("vertical_vane_right", "AUTO")]
        return VERTICAL_WIND_REVERSE.get(mitsubishi_swing_mode)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        mitsubishi_swing_mode = VERTICAL_WIND_OPTIONS[swing_mode]
        await self._execute_command_with_refresh(
            f"set swing mode to {mitsubishi_swing_mode} (vertical)",
            self.coordinator.controller.set_vertical_vane,
            mitsubishi_swing_mode,
            "right",
        )

    @property
    def swing_horizontal_mode(self) -> str | None:
        """Return horizontal vane position or mode."""
        mitsubishi_swing_horizontal_mode = HorizontalWindDirection[self.coordinator.data.get("horizontal_vane", "AUTO")]
        return HORIZONTAL_WIND_REVERSE[mitsubishi_swing_horizontal_mode]

    async def async_set_swing_horizontal_mode(self, swing_horizontal_mode: str) -> None:
        """Set new target horizontal swing operation."""
        mitsubishi_swing_horizontal_mode = HORIZONTAL_WIND_OPTIONS[swing_horizontal_mode]
        await self._execute_command_with_refresh(
            f"set swing mode to {mitsubishi_swing_horizontal_mode} (horizontal)",
            self.coordinator.controller.set_horizontal_vane,
            mitsubishi_swing_horizontal_mode,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attributes = {}

        # Add outdoor temperature if available
        if outdoor_temp := self.coordinator.data.get("outside_temp"):
            attributes["outdoor_temperature"] = outdoor_temp

        # Add power saving mode status
        if power_saving := self.coordinator.data.get("power_saving_mode"):
            attributes["power_saving_mode"] = power_saving

        # Add dehumidifier setting
        if dehum_setting := self.coordinator.data.get("dehumidifier_setting"):
            attributes["dehumidifier_setting"] = dehum_setting

        # Add error information if available
        if error_code := self.coordinator.data.get("error_code"):
            attributes["error_code"] = error_code

        if abnormal_state := self.coordinator.data.get("abnormal_state"):
            attributes["abnormal_state"] = abnormal_state

        # Add energy states if available
        energy_states = self.coordinator.data.get("energy_states")
        if energy_states:
            if "compressor_frequency" in energy_states:
                attributes["compressor_frequency"] = energy_states["compressor_frequency"]
            if "operating" in energy_states:
                attributes["compressor_operating"] = energy_states["operating"]
            if "estimated_power_watts" in energy_states:
                attributes["estimated_power_watts"] = energy_states["estimated_power_watts"]

        # Add device capabilities
        if capabilities := self.coordinator.data.get("capabilities"):
            attributes["supported_modes"] = list(capabilities.keys())

        return attributes


    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self._execute_command_with_refresh(
            "turn on device", self.coordinator.controller.set_power, True
        )

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self._execute_command_with_refresh(
            "turn off device", self.coordinator.controller.set_power, False
        )

    async def _update_coordinator_from_controller_state(self) -> None:
        """Update coordinator data from controller's current state without fetching from device."""
        try:
            # Get the current state summary from the controller (which was updated by the command)
            summary = await self.hass.async_add_executor_job(
                self.coordinator.controller.get_status_summary
            )

            # Update the coordinator's data directly
            self.coordinator.data = summary

            # Trigger state update for all entities
            self.coordinator.async_update_listeners()

            _LOGGER.debug(
                f"Updated coordinator from controller state: target_temp={summary.get('target_temp')}°C"
            )

        except Exception as e:
            _LOGGER.error(f"Error updating coordinator from controller state: {e}")
            # Fall back to regular refresh if there's an error
            await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
