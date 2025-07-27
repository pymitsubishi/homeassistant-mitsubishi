"""Sensor platform for Mitsubishi Air Conditioner integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.info("Setting up Mitsubishi sensors with coordinator data available: %s", coordinator.data is not None)
    
    # Create all sensors, handling any that fail gracefully
    sensors = []
    
    # Standard sensors
    sensor_classes = [
        ("room_temperature", MitsubishiRoomTemperatureSensor),
        ("outdoor_temperature", MitsubishiOutdoorTemperatureSensor), 
        ("error_status", MitsubishiErrorSensor),
        ("dehumidifier_level", MitsubishiDehumidifierLevelSensor),
        ("unit_info", MitsubishiUnitInfoSensor),
        ("firmware_version", MitsubishiFirmwareVersionSensor),
        ("unit_type", MitsubishiUnitTypeSensor),
        ("wifi_info", MitsubishiWifiInfoSensor),
    ]
    
    for sensor_name, sensor_class in sensor_classes:
        try:
            _LOGGER.debug("Creating sensor: %s", sensor_name)
            sensor = sensor_class(coordinator, config_entry)
            if sensor is not None:
                sensors.append(sensor)
                _LOGGER.debug("Successfully created sensor: %s", sensor_name)
            else:
                _LOGGER.warning("Sensor %s returned None", sensor_name)
        except Exception as e:
            _LOGGER.exception("Failed to create %s sensor: %s", sensor_name, e)
    
    _LOGGER.info("Created %d sensors out of %d attempted", len(sensors), len(sensor_classes))
    async_add_entities(sensors)


class MitsubishiRoomTemperatureSensor(MitsubishiEntity, SensorEntity):
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
        super().__init__(coordinator, config_entry, "room_temperature")

    @property
    def native_value(self) -> float | None:
        """Return the room temperature."""
        if self.coordinator.data and (room_temp := self.coordinator.data.get("room_temp")):
            return float(room_temp)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}


class MitsubishiOutdoorTemperatureSensor(MitsubishiEntity, SensorEntity):
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
        super().__init__(coordinator, config_entry, "outdoor_temperature")

    @property
    def native_value(self) -> float | None:
        """Return the outdoor temperature."""
        if self.coordinator.data and (outside_temp := self.coordinator.data.get("outside_temp")):
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
        if self.coordinator.data and (dehumidifier_level := self.coordinator.data.get("dehumidifier_setting")):
            return dehumidifier_level
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}


class MitsubishiErrorSensor(MitsubishiEntity, SensorEntity):
    """Error status sensor for Mitsubishi AC."""

    _attr_name = "Error Status"
    _attr_icon = "mdi:alert"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the error status sensor."""
        super().__init__(coordinator, config_entry, "error_status")

    @property
    def native_value(self) -> str | None:
        """Return the error code or 'OK' if no error."""
        if self.coordinator.data and (error_code := self.coordinator.data.get("error_code")):
            return error_code
        return "OK"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "abnormal_state": self.coordinator.data.get("abnormal_state", False) if self.coordinator.data else False
        }


class BaseMitsubishiDiagnosticSensor(MitsubishiEntity, SensorEntity):
    """Base class for diagnostic sensors that use unit_info data."""
    
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def _get_unit_info_data(self) -> tuple[dict, dict]:
        """Get adaptor_info and unit_info dictionaries, handling None coordinator.unit_info."""
        if not self.coordinator.unit_info:
            return {}, {}
        
        adaptor_info = self.coordinator.unit_info.get("adaptor_info", {})
        unit_info = self.coordinator.unit_info.get("unit_info", {})
        return adaptor_info, unit_info
    
    def _filter_none_values(self, attributes: dict) -> dict:
        """Remove None values from attributes dictionary."""
        return {k: v for k, v in attributes.items() if v is not None}
    
    def _get_unavailable_status(self) -> dict:
        """Return status dictionary when unit info is not available."""
        return {"status": "Unit info not available"}


class MitsubishiUnitInfoSensor(BaseMitsubishiDiagnosticSensor):
    """Unit information diagnostic sensor for Mitsubishi AC."""

    _attr_name = "Unit Information"
    _attr_icon = "mdi:information"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the unit info sensor."""
        super().__init__(coordinator, config_entry, "unit_info")

    @property
    def native_value(self) -> str | None:
        """Return the device model as the state value."""
        adaptor_info, _ = self._get_unit_info_data()
        return adaptor_info.get("model", "Unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return comprehensive unit information as attributes."""
        adaptor_info, unit_info = self._get_unit_info_data()
        
        if not adaptor_info and not unit_info:
            return self._get_unavailable_status()
        
        attributes = {}
        
        # Add adaptor information
        if adaptor_info:
            attributes.update({
                "app_version": adaptor_info.get("app_version"),
                "release_version": adaptor_info.get("release_version"),
                "flash_version": adaptor_info.get("flash_version"),
                "boot_version": adaptor_info.get("boot_version"),
                "platform_version": adaptor_info.get("platform_version"),
                "test_version": adaptor_info.get("test_version"),
                "mac_address": adaptor_info.get("mac_address"),
                "device_id": adaptor_info.get("device_id"),
                "manufacturing_date": adaptor_info.get("manufacturing_date"),
                "wifi_channel": adaptor_info.get("wifi_channel"),
                "rssi_dbm": adaptor_info.get("rssi_dbm"),
                "it_comm_status": adaptor_info.get("it_comm_status"),
                "server_operation": adaptor_info.get("server_operation"),
                "server_comm_status": adaptor_info.get("server_comm_status"),
                "hems_comm_status": adaptor_info.get("hems_comm_status"),
                "soi_comm_status": adaptor_info.get("soi_comm_status"),
            })
        
        # Add unit type information
        if unit_info:
            attributes.update({
                "unit_type": unit_info.get("type"),
                "it_protocol_version": unit_info.get("it_protocol_version"),
                "unit_error_code": unit_info.get("error_code"),
            })
        
        return self._filter_none_values(attributes)


class MitsubishiFirmwareVersionSensor(BaseMitsubishiDiagnosticSensor):
    """Firmware version diagnostic sensor for Mitsubishi AC."""

    _attr_name = "Firmware Version"
    _attr_icon = "mdi:chip"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the firmware version sensor."""
        super().__init__(coordinator, config_entry, "firmware_version")

    @property
    def native_value(self) -> str | None:
        """Return the app version as the main state."""
        adaptor_info, _ = self._get_unit_info_data()
        return adaptor_info.get("app_version", "Unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed version information as attributes."""
        adaptor_info, unit_info = self._get_unit_info_data()
        
        if not adaptor_info and not unit_info:
            return self._get_unavailable_status()
        
        attributes = {
            "release_version": adaptor_info.get("release_version"),
            "flash_version": adaptor_info.get("flash_version"),
            "boot_version": adaptor_info.get("boot_version"),
            "platform_version": adaptor_info.get("platform_version"),
            "test_version": adaptor_info.get("test_version"),
            "protocol_version": unit_info.get("it_protocol_version"),
        }
        
        return self._filter_none_values(attributes)


class MitsubishiUnitTypeSensor(BaseMitsubishiDiagnosticSensor):
    """Unit type diagnostic sensor for Mitsubishi AC."""

    _attr_name = "Unit Type"
    _attr_icon = "mdi:air-conditioner"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the unit type sensor."""
        super().__init__(coordinator, config_entry, "unit_type")

    @property
    def native_value(self) -> str | None:
        """Return the unit type."""
        _, unit_info = self._get_unit_info_data()
        return unit_info.get("type", "Unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return unit-related information as attributes."""
        adaptor_info, unit_info = self._get_unit_info_data()
        
        if not adaptor_info and not unit_info:
            return self._get_unavailable_status()
        
        attributes = {
            "model": adaptor_info.get("model"),
            "device_id": adaptor_info.get("device_id"),
            "manufacturing_date": adaptor_info.get("manufacturing_date"),
            "protocol_version": unit_info.get("it_protocol_version"),
            "unit_error_code": unit_info.get("error_code"),
        }
        
        return self._filter_none_values(attributes)


class MitsubishiWifiInfoSensor(BaseMitsubishiDiagnosticSensor):
    """WiFi information diagnostic sensor for Mitsubishi AC."""

    _attr_name = "WiFi Information"
    _attr_icon = "mdi:wifi"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the WiFi info sensor."""
        super().__init__(coordinator, config_entry, "wifi_info")

    @property
    def native_value(self) -> str | None:
        """Return the WiFi signal strength as the main state."""
        adaptor_info, _ = self._get_unit_info_data()
        rssi = adaptor_info.get("rssi_dbm")
        if rssi is not None:
            return f"{rssi} dBm"
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return WiFi and communication status as attributes."""
        adaptor_info, unit_info = self._get_unit_info_data()
        
        if not adaptor_info and not unit_info:
            return self._get_unavailable_status()
        
        attributes = {
            "mac_address": adaptor_info.get("mac_address"),
            "wifi_channel": adaptor_info.get("wifi_channel"),
            "rssi_dbm": adaptor_info.get("rssi_dbm"),
            "it_comm_status": adaptor_info.get("it_comm_status"),
            "server_operation": adaptor_info.get("server_operation"),
            "server_comm_status": adaptor_info.get("server_comm_status"),
            "hems_comm_status": adaptor_info.get("hems_comm_status"),
            "soi_comm_status": adaptor_info.get("soi_comm_status"),
        }
        
        return self._filter_none_values(attributes)

