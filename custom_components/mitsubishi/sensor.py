"""Sensor platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity
from .utils import (
    filter_none_values,
    has_energy_state,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.info(
        "Setting up Mitsubishi sensors with coordinator data available: %s",
        coordinator.data is not None,
    )

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
        # SwiCago-inspired enhanced sensors
        ("compressor_frequency", MitsubishiCompressorFrequencySensor),
        ("estimated_power", MitsubishiEstimatedPowerSensor),
        ("mode_raw_value", MitsubishiModeRawValueSensor),
        ("temperature_mode", MitsubishiTemperatureModeSensor),
        # Energy monitoring sensors (requires pymitsubishi >= 0.1.7 with energy data)
        ("energy_total", MitsubishiEnergyTotalSensor),
        ("energy_cooling", MitsubishiEnergyCoolingSensor),
        ("energy_heating", MitsubishiEnergyHeatingSensor),
        ("energy_auto", MitsubishiEnergyAutoSensor),
        ("energy_dry", MitsubishiEnergyDrySensor),
        ("energy_fan", MitsubishiEnergyFanSensor),
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
        if self.coordinator.data and (
            dehumidifier_level := self.coordinator.data.get("dehumidifier_setting")
        ):
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
            "abnormal_state": self.coordinator.data.get("abnormal_state", False)
            if self.coordinator.data
            else False
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
        return filter_none_values(attributes)

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
            attributes.update(
                {
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
                }
            )

        # Add unit type information
        if unit_info:
            attributes.update(
                {
                    "unit_type": unit_info.get("type"),
                    "it_protocol_version": unit_info.get("it_protocol_version"),
                    "unit_error_code": unit_info.get("error_code"),
                }
            )

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


# SwiCago-inspired enhanced sensors
class MitsubishiCompressorFrequencySensor(MitsubishiEntity, SensorEntity):
    """Compressor frequency sensor for Mitsubishi AC (SwiCago enhancement)."""

    _attr_name = "Compressor Frequency"
    _attr_icon = "mdi:fan"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "Hz"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the compressor frequency sensor."""
        super().__init__(coordinator, config_entry, "compressor_frequency")

    @property
    def native_value(self) -> int | None:
        """Return the compressor frequency."""
        if (
            self.coordinator.data
            and (energy_states := self.coordinator.data.get("energy_states"))
            and energy_states.get("compressor_frequency") is not None
        ):
            return energy_states["compressor_frequency"]
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {"source": "SwiCago enhancement"}
        if has_energy_state(self.coordinator):
            attrs["operating"] = self.coordinator.controller.state.energy.operating
        return attrs


class MitsubishiEstimatedPowerSensor(MitsubishiEntity, SensorEntity):
    """Estimated power consumption sensor for Mitsubishi AC (SwiCago enhancement)."""

    _attr_name = "Estimated Power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = "W"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the estimated power sensor."""
        super().__init__(coordinator, config_entry, "estimated_power")

    @property
    def native_value(self) -> float | None:
        """Return the estimated power consumption."""
        if (
            self.coordinator.data
            and (energy_states := self.coordinator.data.get("energy_states"))
            and energy_states.get("estimated_power_watts") is not None
        ):
            return energy_states["estimated_power_watts"]
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {
            "source": "SwiCago enhancement",
            "estimation_method": "Compressor frequency + mode + fan speed",
            "accuracy": "Rough estimate - varies with conditions",
        }
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
                    "operating_status": energy.operating,
                }
            )
        return attrs


class MitsubishiModeRawValueSensor(MitsubishiEntity, SensorEntity):
    """Mode raw value sensor for Mitsubishi AC (SwiCago enhancement)."""

    _attr_name = "Mode Raw Value"
    _attr_icon = "mdi:code-brackets"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the mode raw value sensor."""
        super().__init__(coordinator, config_entry, "mode_raw_value")

    @property
    def native_value(self) -> str | None:
        """Return the raw mode value in hex format."""
        if (
            self.coordinator.data
            and (raw_value := self.coordinator.data.get("mode_raw_value")) is not None
        ):
            return f"0x{raw_value:02x}"
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.native_value is not None

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
            attrs["i_see_sensor_active"] = general.i_see_sensor
            if general.drive_mode:
                attrs["parsed_mode"] = general.drive_mode.name
            attrs["wide_vane_adjustment"] = general.wide_vane_adjustment
        return attrs


class MitsubishiTemperatureModeSensor(MitsubishiEntity, SensorEntity):
    """Temperature mode sensor for Mitsubishi AC (SwiCago enhancement)."""

    _attr_name = "Temperature Mode"
    _attr_icon = "mdi:thermometer-lines"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the temperature mode sensor."""
        super().__init__(coordinator, config_entry, "temperature_mode")

    @property
    def native_value(self) -> str | None:
        """Return the temperature parsing mode."""
        if (
            self.coordinator.data
            and (temp_mode := self.coordinator.data.get("temperature_mode")) is not None
        ):
            return temp_mode.capitalize()
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {
            "source": "SwiCago enhancement",
            "description": "Direct mode uses precise temperature values, Segment mode uses predefined steps",
        }
        if (
            hasattr(self.coordinator, "controller")
            and hasattr(self.coordinator.controller, "state")
            and self.coordinator.controller.state
            and hasattr(self.coordinator.controller.state, "general")
            and self.coordinator.controller.state.general
        ):
            general = self.coordinator.controller.state.general
            if general.temperature:
                attrs["current_temperature_celsius"] = general.temperature / 10.0
        return attrs


# Energy monitoring sensors
class BaseMitsubishiEnergySensor(MitsubishiEntity, SensorEntity):
    """Base class for energy consumption sensors."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = "total_increasing"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_key: str,
        energy_type: str,
    ) -> None:
        """Initialize the energy sensor."""
        self._energy_type = energy_type
        super().__init__(coordinator, config_entry, sensor_key)

    def _get_energy_value(self, key: str) -> float | None:
        """Get energy value from coordinator state."""
        if (
            hasattr(self.coordinator, "controller")
            and hasattr(self.coordinator.controller, "state")
            and self.coordinator.controller.state
            and hasattr(self.coordinator.controller.state, "energy")
            and self.coordinator.controller.state.energy
        ):
            energy_state = self.coordinator.controller.state.energy
            if hasattr(energy_state, key):
                value = getattr(energy_state, key)
                # Convert from Wh to kWh
                return value / 1000.0 if value is not None else None
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {
            "source": "Energy monitoring",
            "energy_type": self._energy_type,
            "unit_conversion": "Wh to kWh (÷1000)",
        }
        if (
            hasattr(self.coordinator, "controller")
            and hasattr(self.coordinator.controller, "state")
            and self.coordinator.controller.state
            and hasattr(self.coordinator.controller.state, "energy")
            and self.coordinator.controller.state.energy
        ):
            energy = self.coordinator.controller.state.energy
            attrs["operating_status"] = energy.operating
            attrs["compressor_frequency"] = energy.compressor_frequency
        return attrs


class MitsubishiEnergyTotalSensor(BaseMitsubishiEnergySensor):
    """Total energy consumption sensor for Mitsubishi AC."""

    _attr_name = "Total Energy"
    _attr_icon = "mdi:lightning-bolt"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the total energy sensor."""
        super().__init__(coordinator, config_entry, "energy_total", "total")

    @property
    def native_value(self) -> float | None:
        """Return the total energy consumption."""
        return self._get_energy_value("energy_total_kWh")


class MitsubishiEnergyCoolingSensor(BaseMitsubishiEnergySensor):
    """Cooling energy consumption sensor for Mitsubishi AC."""

    _attr_name = "Cooling Energy"
    _attr_icon = "mdi:snowflake"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the cooling energy sensor."""
        super().__init__(coordinator, config_entry, "energy_cooling", "cooling")

    @property
    def native_value(self) -> float | None:
        """Return the cooling energy consumption."""
        return self._get_energy_value("energy_total_cooling_kWh")


class MitsubishiEnergyHeatingSensor(BaseMitsubishiEnergySensor):
    """Heating energy consumption sensor for Mitsubishi AC."""

    _attr_name = "Heating Energy"
    _attr_icon = "mdi:fire"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the heating energy sensor."""
        super().__init__(coordinator, config_entry, "energy_heating", "heating")

    @property
    def native_value(self) -> float | None:
        """Return the heating energy consumption."""
        return self._get_energy_value("energy_total_heating_kWh")


class MitsubishiEnergyAutoSensor(BaseMitsubishiEnergySensor):
    """Auto mode energy consumption sensor for Mitsubishi AC."""

    _attr_name = "Auto Mode Energy"
    _attr_icon = "mdi:thermostat-auto"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the auto mode energy sensor."""
        super().__init__(coordinator, config_entry, "energy_auto", "auto")

    @property
    def native_value(self) -> float | None:
        """Return the auto mode energy consumption."""
        return self._get_energy_value("energy_total_auto_kWh")


class MitsubishiEnergyDrySensor(BaseMitsubishiEnergySensor):
    """Dry mode energy consumption sensor for Mitsubishi AC."""

    _attr_name = "Dry Mode Energy"
    _attr_icon = "mdi:water-percent"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the dry mode energy sensor."""
        super().__init__(coordinator, config_entry, "energy_dry", "dry")

    @property
    def native_value(self) -> float | None:
        """Return the dry mode energy consumption."""
        return self._get_energy_value("energy_total_dry_kWh")


class MitsubishiEnergyFanSensor(BaseMitsubishiEnergySensor):
    """Fan mode energy consumption sensor for Mitsubishi AC."""

    _attr_name = "Fan Mode Energy"
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the fan mode energy sensor."""
        super().__init__(coordinator, config_entry, "energy_fan", "fan")

    @property
    def native_value(self) -> float | None:
        """Return the fan mode energy consumption."""
        return self._get_energy_value("energy_total_fan_kWh")
