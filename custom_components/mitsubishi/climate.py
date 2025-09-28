"""Climate platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
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
    AutoMode,
    DriveMode,
    HorizontalWindDirection,
    PowerOnOff,
    VerticalWindDirection,
    WindSpeed,
)

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity

_LOGGER = logging.getLogger(__name__)

# Mapping from HA HVAC modes to Mitsubishi modes
MODE_HA_TO_MITSUBISHI = {
    # HA has Off as well, that we need to handle differently
    HVACMode.HEAT: DriveMode.HEATER,
    HVACMode.COOL: DriveMode.COOLER,
    HVACMode.AUTO: DriveMode.AUTO,
    HVACMode.DRY: DriveMode.DEHUM,
    HVACMode.FAN_ONLY: DriveMode.FAN,
}
MODE_MITSUBISHI_TO_HA = {v: k for k, v in MODE_HA_TO_MITSUBISHI.items()}
ACTION_MITSUBISHI_TO_HA = {
    DriveMode.COOLER: HVACAction.COOLING,
    DriveMode.HEATER: HVACAction.HEATING,
    DriveMode.DEHUM: HVACAction.DRYING,
    DriveMode.FAN: HVACAction.FAN,
}

FAN_SPEED_HA_TO_MITSUBISHI = {
    FAN_AUTO: WindSpeed.AUTO,
    FAN_LOW: WindSpeed.S1,
    "low-medium": WindSpeed.S2,
    FAN_MEDIUM: WindSpeed.S3,
    FAN_HIGH: WindSpeed.S4,
    "full": WindSpeed.FULL,
}
FAN_SPEED_MITSUBISHI_TO_HA = {v: k for k, v in FAN_SPEED_HA_TO_MITSUBISHI.items()}

HSWING_HA_TO_MITSUBISHI = {
    "auto": HorizontalWindDirection.AUTO,
    "far left": HorizontalWindDirection.FAR_LEFT,
    "left": HorizontalWindDirection.LEFT,
    "center": HorizontalWindDirection.CENTER,
    "right": HorizontalWindDirection.RIGHT,
    "far right": HorizontalWindDirection.FAR_RIGHT,
    "left and center": HorizontalWindDirection.LEFT_CENTER,
    "center and right": HorizontalWindDirection.CENTER_RIGHT,
    "left, center and right": HorizontalWindDirection.LEFT_CENTER_RIGHT,
    "left and right": HorizontalWindDirection.LEFT_RIGHT,
    "swing": HorizontalWindDirection.SWING,
}
HSWING_MITSUBISHI_TO_HA = {v: k for k, v in HSWING_HA_TO_MITSUBISHI.items()}

VSWING_HA_TO_MITSUBISHI = {
    "auto": VerticalWindDirection.AUTO,
    "1": VerticalWindDirection.V1,
    "2": VerticalWindDirection.V2,
    "3": VerticalWindDirection.V3,
    "4": VerticalWindDirection.V4,
    "5": VerticalWindDirection.V5,
    "swing": VerticalWindDirection.SWING,
}
VSWING_MITSUBISHI_TO_HA = {v: k for k, v in VSWING_HA_TO_MITSUBISHI.items()}


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
    _attr_icon = "mdi:air-conditioner"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 16.0
    _attr_max_temp = 32.0
    _attr_hvac_modes = [
        HVACMode.OFF,
        *MODE_HA_TO_MITSUBISHI.keys(),
    ]
    _attr_fan_modes = list(FAN_SPEED_HA_TO_MITSUBISHI.keys())
    _attr_swing_modes = list(VSWING_HA_TO_MITSUBISHI.keys())
    _attr_swing_horizontal_modes = list(HSWING_HA_TO_MITSUBISHI.keys())

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.SWING_HORIZONTAL_MODE  # type: ignore[attr-defined]
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
        try:
            return self.coordinator.data.sensors.room_temperature
        except AttributeError:
            return None

    @property
    def target_temperature(self) -> float | None:
        try:
            return self.coordinator.data.general.temperature
        except AttributeError:
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
    def hvac_mode(self) -> HVACMode | None:
        """
        Return hvac operation i.e. heat, cool mode.
        Note that HA sees "off" as a mode; Mitsubishi has a separate PowerOnOff field, so join these
        """
        try:
            if self.coordinator.data.general.power_on_off == PowerOnOff.OFF:
                return HVACMode.OFF
            return MODE_MITSUBISHI_TO_HA[self.coordinator.data.general.drive_mode]
        except AttributeError:
            return None

    async def async_turn_on(self) -> None:
        await self._execute_command_with_refresh(
            "turn on device", self.coordinator.controller.set_power, True
        )

    async def async_turn_off(self) -> None:
        await self._execute_command_with_refresh(
            "turn off device", self.coordinator.controller.set_power, False
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self._execute_command_with_refresh(
                f"set HVAC mode to {hvac_mode}", self.coordinator.controller.set_power, False
            )
        else:
            # Set the mode
            await self._execute_command_with_refresh(
                f"set HVAC mode to {hvac_mode}",
                self.coordinator.controller.set_mode,
                MODE_HA_TO_MITSUBISHI[hvac_mode],
            )

            # Turn on if currently off
            # Set mode before setting power, so the unit can start in the correct mode
            if self.hvac_mode == HVACMode.OFF:
                await self._execute_command_with_refresh(
                    "turn on device before setting mode",
                    self.coordinator.controller.set_power,
                    True,
                )

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF

        if self.hvac_mode == HVACMode.FAN_ONLY:
            return HVACAction.FAN

        # Check if we have energy state data to determine if compressor is running
        try:
            if not self.coordinator.data.energy.operating:
                return HVACAction.IDLE
        except AttributeError:
            pass

        if self.hvac_mode == HVACMode.AUTO:
            MAP = {
                AutoMode.SWITCHING: None,
                AutoMode.AUTO_HEATING: HVACAction.HEATING,
                AutoMode.AUTO_COOLING: HVACAction.COOLING,
            }
            return MAP[self.coordinator.data.auto_state.auto_mode]

        try:
            return ACTION_MITSUBISHI_TO_HA[self.coordinator.data.general.drive_mode]
        except AttributeError:
            return None

    @property
    def fan_mode(self) -> str | None:
        try:
            return FAN_SPEED_MITSUBISHI_TO_HA[self.coordinator.data.general.wind_speed]
        except AttributeError:
            return None

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self._execute_command_with_refresh(
            f"set fan mode to {fan_mode}",
            self.coordinator.controller.set_fan_speed,
            FAN_SPEED_HA_TO_MITSUBISHI[fan_mode],
        )

    @property
    def swing_mode(self) -> str | None:
        try:
            return VSWING_MITSUBISHI_TO_HA[self.coordinator.data.general.vertical_wind_direction]
        except AttributeError:
            return None

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        await self._execute_command_with_refresh(
            f"set swing mode to {swing_mode}",
            self.coordinator.controller.set_vertical_vane,
            VSWING_HA_TO_MITSUBISHI[swing_mode],
        )

    @property
    def swing_horizontal_mode(self) -> str | None:
        try:
            return HSWING_MITSUBISHI_TO_HA[self.coordinator.data.general.horizontal_wind_direction]
        except AttributeError:
            return None

    async def async_set_swing_horizontal_mode(self, swing_horizontal_mode: str) -> None:
        await self._execute_command_with_refresh(
            f"set horizontal swing mode to {swing_horizontal_mode}",
            self.coordinator.controller.set_horizontal_vane,
            HSWING_HA_TO_MITSUBISHI[swing_horizontal_mode],
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {}

        try:
            attrs["outdoor_temperature"] = self.coordinator.data.sensors.outside_temperature
        except AttributeError:
            pass

        try:
            attrs["power_saving_mode"] = self.coordinator.data.general.is_power_saving
            attrs["dehumidifier_setting"] = self.coordinator.data.general.dehum_setting
        except AttributeError:
            pass

        try:
            attrs["error_code"] = self.coordinator.data.errors.error_code
            attrs["abnormal_state"] = self.coordinator.data.errors.is_abnormal_state
        except AttributeError:
            pass

        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
