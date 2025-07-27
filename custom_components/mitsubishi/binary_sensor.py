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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator


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
        ]
    )


class MitsubishiPowerSavingBinarySensor(
    CoordinatorEntity[MitsubishiDataUpdateCoordinator], BinarySensorEntity
):
    """Power saving mode binary sensor for Mitsubishi AC."""

    _attr_name = "Power Saving Mode"
    _attr_icon = "mdi:leaf"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the power saving binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('mac', config_entry.data['host'])}_power_saving"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data.get("mac", config_entry.data["host"]))},
        }

    @property
    def is_on(self) -> bool:
        """Return true if power saving mode is enabled."""
        return self.coordinator.data.get("power_saving_mode", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}


class MitsubishiErrorBinarySensor(
    CoordinatorEntity[MitsubishiDataUpdateCoordinator], BinarySensorEntity
):
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
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('mac', config_entry.data['host'])}_error_state"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data.get("mac", config_entry.data["host"]))},
        }

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
