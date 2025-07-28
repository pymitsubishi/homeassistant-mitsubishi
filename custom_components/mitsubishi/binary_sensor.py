"""Binary sensor platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity
from .utils import (
    has_controller_state,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi binary sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            MitsubishiPowerSavingBinarySensor(coordinator, config_entry),
            MitsubishiErrorBinarySensor(coordinator, config_entry),
            # SwiCago-inspired enhanced binary sensors
            MitsubishiISeeActiveBinarySensor(coordinator, config_entry),
            MitsubishiOperatingBinarySensor(coordinator, config_entry),
            MitsubishiWideVaneAdjustmentBinarySensor(coordinator, config_entry),
        ]
    )


class MitsubishiPowerSavingBinarySensor(MitsubishiEntity, BinarySensorEntity):
    """Power saving mode binary sensor for Mitsubishi AC."""

    _attr_name = "Power Saving Mode"
    _attr_icon = "mdi:leaf"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the power saving binary sensor."""
        super().__init__(coordinator, config_entry, "power_saving_mode")

    @property
    def is_on(self) -> bool:
        """Return true if power saving mode is enabled."""
        return self.coordinator.data.get("power_saving_mode", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}


class MitsubishiErrorBinarySensor(MitsubishiEntity, BinarySensorEntity):
    """Error state binary sensor for Mitsubishi AC."""

    _attr_name = "Error State"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert-circle"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the error binary sensor."""
        super().__init__(coordinator, config_entry, "error_state")

    @property
    def is_on(self) -> bool:
        """Return true if there is an error or abnormal state."""
        abnormal_state = self.coordinator.data.get("abnormal_state", False)
        error_code = self.coordinator.data.get("error_code", "8000")
        # Error code "8000" typically means no error
        has_error = error_code != "8000" and error_code != "OK"
        return abnormal_state or has_error

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "error_code": self.coordinator.data.get("error_code", "8000"),
            "abnormal_state": self.coordinator.data.get("abnormal_state", False),
        }


# SwiCago-inspired enhanced binary sensors
class MitsubishiISeeActiveBinarySensor(MitsubishiEntity, BinarySensorEntity):
    """i-See sensor active binary sensor for Mitsubishi AC (SwiCago enhancement)."""

    _attr_name = "i-See Sensor Active"
    _attr_icon = "mdi:eye"
    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the i-See sensor binary sensor."""
        super().__init__(coordinator, config_entry, "i_see_active")

    @property
    def is_on(self) -> bool:
        """Return true if i-See sensor is active."""
        if (
            self.coordinator.data
            and (i_see_active := self.coordinator.data.get("i_see_sensor_active")) is not None
        ):
            return i_see_active
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return has_controller_state(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {"source": "SwiCago enhancement"}
        if (
            hasattr(self.coordinator, "controller")
            and hasattr(self.coordinator.controller, "state")
            and self.coordinator.controller.state
            and hasattr(self.coordinator.controller.state, "general")
            and self.coordinator.controller.state.general
        ):
            general = self.coordinator.controller.state.general
            if general.mode_raw_value is not None:
                attrs["mode_raw_value"] = f"0x{general.mode_raw_value:02x}"
            if general.drive_mode:
                attrs["parsed_mode"] = general.drive_mode.name
        return attrs


class MitsubishiOperatingBinarySensor(MitsubishiEntity, BinarySensorEntity):
    """Operating status binary sensor for Mitsubishi AC (SwiCago enhancement)."""

    _attr_name = "Operating Status"
    _attr_icon = "mdi:power"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the operating status binary sensor."""
        super().__init__(coordinator, config_entry, "operating_status")

    @property
    def is_on(self) -> bool:
        """Return true if the unit is actively operating."""
        if (
            self.coordinator.data
            and (energy_states := self.coordinator.data.get("energy_states"))
            and energy_states.get("operating") is not None
        ):
            return energy_states["operating"]
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return has_controller_state(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {"source": "SwiCago enhancement"}
        if (
            hasattr(self.coordinator, "controller")
            and hasattr(self.coordinator.controller, "state")
            and self.coordinator.controller.state
            and hasattr(self.coordinator.controller.state, "energy")
            and self.coordinator.controller.state.energy
        ):
            energy = self.coordinator.controller.state.energy
            attrs.update(
                {
                    "compressor_frequency": energy.compressor_frequency,
                    "estimated_power_watts": energy.estimated_power_watts,
                }
            )
        return attrs


class MitsubishiWideVaneAdjustmentBinarySensor(MitsubishiEntity, BinarySensorEntity):
    """Wide vane adjustment binary sensor for Mitsubishi AC (SwiCago enhancement)."""

    _attr_name = "Wide Vane Adjustment"
    _attr_icon = "mdi:tune-vertical"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the wide vane adjustment binary sensor."""
        super().__init__(coordinator, config_entry, "wide_vane_adjustment")

    @property
    def is_on(self) -> bool:
        """Return true if wide vane adjustment is active."""
        if (
            self.coordinator.data
            and (wide_vane := self.coordinator.data.get("wide_vane_adjustment")) is not None
        ):
            return wide_vane
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return has_controller_state(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {"source": "SwiCago enhancement"}
        if (
            hasattr(self.coordinator, "controller")
            and hasattr(self.coordinator.controller, "state")
            and self.coordinator.controller.state
            and hasattr(self.coordinator.controller.state, "general")
            and self.coordinator.controller.state.general
        ):
            general = self.coordinator.controller.state.general
            if general.horizontal_wind_direction:
                attrs["horizontal_wind_direction"] = general.horizontal_wind_direction.name
        return attrs
