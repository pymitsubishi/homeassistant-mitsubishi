"""Sensor platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
import typing
from enum import StrEnum
from typing import Any

import pymitsubishi
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
    _LOGGER.debug(
        "Setting up Mitsubishi sensors with coordinator data available: %s",
        coordinator.data is not None,
    )

    sensors: list[SensorEntity] = []

    sensors.append(
        MitsubishiSensor(
            coordinator,
            config_entry,
            "Inside Temperature 1",
            "inside_temperature_1_fine",
            lambda d: float(d.sensors.inside_temperature_1_fine),
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
        )
    )
    sensors.append(
        MitsubishiSensor(
            coordinator,
            config_entry,
            "Inside Temperature 2",
            "inside_temperature_2",
            lambda d: float(d.sensors.inside_temperature_2),
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
    )
    sensors.append(
        MitsubishiSensor(
            coordinator,
            config_entry,
            "Outside Temperature",
            "outside_temp",
            lambda d: float(d.sensors.outside_temperature),
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
        )
    )
    sensors.append(
        MitsubishiSensor(
            coordinator,
            config_entry,
            "Power",
            "power",
            lambda d: float(d.energy.power_watt),
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            sensor_state_class=SensorStateClass.MEASUREMENT,
        )
    )
    sensors.append(
        MitsubishiSensor(
            coordinator,
            config_entry,
            "Energy",
            "energy",
            lambda d: float(d.energy.energy_hecto_watt_hour) * 0.1,
            SensorDeviceClass.ENERGY,
            UnitOfEnergy.KILO_WATT_HOUR,
            sensor_state_class=SensorStateClass.TOTAL_INCREASING,
        )
    )
    sensors.append(
        MitsubishiSensor(
            coordinator,
            config_entry,
            "Runtime",
            "runtime_minutes",
            lambda d: float(d.sensors.runtime_minutes),
            SensorDeviceClass.DURATION,
            UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
    )
    sensors.append(
        MitsubishiSensor(
            coordinator,
            config_entry,
            "Power mode",
            "power_mode",
            lambda d: float(d.auto_state.power_mode),
            entity_category=EntityCategory.DIAGNOSTIC,
            sensor_state_class=SensorStateClass.MEASUREMENT,
        )
    )

    sensors.append(MitsubishiErrorSensor(coordinator, config_entry))

    async_add_entities(sensors)


class MitsubishiSensor(MitsubishiEntity, SensorEntity):
    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_name: str,
        key: str,
        getter: typing.Callable[[pymitsubishi.ParsedDeviceState], float | None],
        device_class: SensorDeviceClass | None = None,
        native_unit_of_measurement: StrEnum | str | None = None,
        entity_category: EntityCategory | None = None,
        sensor_state_class: SensorStateClass | None = None,
    ) -> None:
        self._attr_name = sensor_name
        self._getter = getter
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = native_unit_of_measurement
        self._attr_entity_category = entity_category
        self._attr_state_class = sensor_state_class
        super().__init__(coordinator, config_entry, key)

    @property
    def native_value(self) -> float | None:
        try:
            return self._getter(self.coordinator.data)
        except (TypeError, KeyError, AttributeError):
            return None


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
        try:
            return self.coordinator.data.errors.error_code
        except (TypeError, KeyError, AttributeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        try:
            return {"abnormal_state": self.coordinator.data.errors.is_abnormal_state}
        except (TypeError, KeyError, AttributeError):
            return None
