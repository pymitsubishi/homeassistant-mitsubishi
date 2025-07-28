"""Climate platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_VERTICAL,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pymitsubishi import (
    DriveMode,
    HorizontalWindDirection,
    PowerOnOff,
    VerticalWindDirection,
    WindSpeed,
)

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator

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

# Reverse mapping for state reporting
MITSUBISHI_TO_HVAC_MODE = {
    DriveMode.HEATER: HVACMode.HEAT,
    DriveMode.COOLER: HVACMode.COOL,
    DriveMode.AUTO: HVACMode.AUTO,
    DriveMode.AUTO_COOLER: HVACMode.COOL,
    DriveMode.AUTO_HEATER: HVACMode.HEAT,
    DriveMode.DEHUM: HVACMode.DRY,
    DriveMode.FAN: HVACMode.FAN_ONLY,
}

# Fan speed mapping
FAN_SPEED_MAP = {
    FAN_AUTO: WindSpeed.AUTO,
    FAN_LOW: WindSpeed.LEVEL_1,
    FAN_MEDIUM: WindSpeed.LEVEL_2,
    FAN_HIGH: WindSpeed.LEVEL_3,
    "full": WindSpeed.LEVEL_FULL,
}

MITSUBISHI_TO_FAN_MODE = {
    WindSpeed.AUTO: FAN_AUTO,
    WindSpeed.LEVEL_1: FAN_LOW,
    WindSpeed.LEVEL_2: FAN_MEDIUM,
    WindSpeed.LEVEL_3: FAN_HIGH,
    WindSpeed.LEVEL_FULL: FAN_HIGH,
}

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


class MitsubishiClimate(CoordinatorEntity[MitsubishiDataUpdateCoordinator], ClimateEntity):
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
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH, "full"]
    _attr_swing_modes = [SWING_OFF, SWING_VERTICAL, SWING_HORIZONTAL, SWING_BOTH]

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data.get("mac", config_entry.data["host"]))},
        }
        self._attr_unique_id = f"{coordinator.data.get('mac', config_entry.data['host'])}_climate"

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
                return MITSUBISHI_TO_HVAC_MODE.get(drive_mode, HVACMode.OFF)
            except (KeyError, ValueError):
                return HVACMode.OFF

        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF

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

    @property
    def swing_mode(self) -> str:
        """Return the swing setting."""
        # This is a simplified swing mode - in reality, Mitsubishi has separate
        # horizontal and vertical swing controls
        return SWING_OFF  # Default for now, can be enhanced later

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

        # Add device capabilities
        if capabilities := self.coordinator.data.get("capabilities"):
            attributes["supported_modes"] = list(capabilities.keys())

        return attributes

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self.hass.async_add_executor_job(
            self.coordinator.controller.set_temperature, temperature
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.hass.async_add_executor_job(self.coordinator.controller.set_power, False)
        else:
            # Turn on if currently off
            if self.hvac_mode == HVACMode.OFF:
                await self.hass.async_add_executor_job(self.coordinator.controller.set_power, True)

            # Set the mode
            if hvac_mode in HVAC_MODE_MAP:
                drive_mode = HVAC_MODE_MAP[hvac_mode]
                if isinstance(drive_mode, DriveMode):
                    await self.hass.async_add_executor_job(
                        self.coordinator.controller.set_mode, drive_mode
                    )

        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        if fan_mode in FAN_SPEED_MAP:
            wind_speed = FAN_SPEED_MAP[fan_mode]
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_fan_speed, wind_speed
            )
            await self.coordinator.async_request_refresh()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        # This is a placeholder implementation
        # Real implementation would need to handle vertical and horizontal vanes separately
        if swing_mode == SWING_VERTICAL:
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_vertical_vane, VerticalWindDirection.SWING, "right"
            )
        elif swing_mode == SWING_HORIZONTAL:
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_horizontal_vane, HorizontalWindDirection.LCR_S
            )
        elif swing_mode == SWING_BOTH:
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_vertical_vane, VerticalWindDirection.SWING, "right"
            )
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_horizontal_vane, HorizontalWindDirection.LCR_S
            )
        # SWING_OFF would set them to AUTO or a fixed position

        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self.hass.async_add_executor_job(self.coordinator.controller.set_power, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.hass.async_add_executor_job(self.coordinator.controller.set_power, False)
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
