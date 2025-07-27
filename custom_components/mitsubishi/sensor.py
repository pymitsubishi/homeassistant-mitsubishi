"""Sensor platform for Mitsubishi Air Conditioner integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            MitsubishiRoomTemperatureSensor(coordinator, config_entry),
            MitsubishiOutdoorTemperatureSensor(coordinator, config_entry),
            MitsubishiErrorSensor(coordinator, config_entry),
            MitsubishiDehumidifierLevelSensor(coordinator, config_entry),
        ]
    )


class MitsubishiRoomTemperatureSensor(CoordinatorEntity[MitsubishiDataUpdateCoordinator], SensorEntity):
    """Room temperature sensor for Mitsubishi AC."""

    _attr_name = "Room Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the room temperature sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('mac', config_entry.data['host'])}_room_temp"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data.get("mac", config_entry.data["host"]))},
        }

    @property
    def native_value(self) -> float | None:
        """Return the room temperature."""
        if room_temp := self.coordinator.data.get("room_temp"):
            return float(room_temp)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}


class MitsubishiOutdoorTemperatureSensor(CoordinatorEntity[MitsubishiDataUpdateCoordinator], SensorEntity):
    """Outdoor temperature sensor for Mitsubishi AC."""

    _attr_name = "Outdoor Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the outdoor temperature sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('mac', config_entry.data['host'])}_outdoor_temp"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data.get("mac", config_entry.data["host"]))},
        }

    @property
    def native_value(self) -> float | None:
        """Return the outdoor temperature."""
        if outside_temp := self.coordinator.data.get("outside_temp"):
            return float(outside_temp)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}


class MitsubishiDehumidifierLevelSensor(MitsubishiEntity, SensorEntity):
    """Dehumidifier level sensor for Mitsubishi AC."""

    _attr_name = "Dehumidifier Level"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the dehumidifier level sensor."""
        super().__init__(coordinator, config_entry, "dehumidifier_level")

    @property
    def native_value(self) -> int | None:
        """Return the current dehumidifier setting."""
        if dehumidifier_level := self.coordinator.data.get("dehumidifier_setting"):
            return dehumidifier_level
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}


class MitsubishiErrorSensor(CoordinatorEntity[MitsubishiDataUpdateCoordinator], SensorEntity):
    """Error status sensor for Mitsubishi AC."""

    _attr_name = "Error Status"
    _attr_icon = "mdi:alert"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the error status sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('mac', config_entry.data['host'])}_error_status"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data.get("mac", config_entry.data["host"]))},
        }

    @property
    def native_value(self) -> str | None:
        """Return the error code or 'OK' if no error."""
        if error_code := self.coordinator.data.get("error_code"):
            return error_code
        return "OK"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "abnormal_state": self.coordinator.data.get("abnormal_state", False)
        }

