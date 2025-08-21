"""Binary sensor platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import typing

import pymitsubishi
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi binary sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = []

    sensors.append(MitsubishiBinarySensor(
        coordinator, config_entry,
        "Error State", "error_state",
        lambda d: d.errors.is_abnormal_state,
        icon="mdi:warning", device_class=BinarySensorDeviceClass.PROBLEM,
    ))
    sensors.append(MitsubishiBinarySensor(
        coordinator, config_entry,
        "i-See Sensor Active","i_see_active",
        lambda d: d.general.i_see_sensor,
        icon="mdi:eye", device_class=BinarySensorDeviceClass.MOTION,
    ))
    sensors.append(MitsubishiBinarySensor(
        coordinator, config_entry,
        "Operating Status", "operating",
        lambda d : d.energy.operating,
        icon="mdi:power", device_class=BinarySensorDeviceClass.RUNNING,
    ))
    sensors.append(MitsubishiBinarySensor(
        coordinator, config_entry,
        "Wide Vane Adjustment", "wide_vane_adjustment",
        lambda d: d.general.wide_vane_adjustment,
        icon="mdi:tune-vertical",
    ))

    async_add_entities(sensors)


class MitsubishiBinarySensor(MitsubishiEntity, BinarySensorEntity):
    def __init__(
            self,
            coordinator: MitsubishiDataUpdateCoordinator,
            config_entry: ConfigEntry,
            sensor_name: str,
            key: str,
            getter: typing.Callable[[pymitsubishi.ParsedDeviceState], bool | None],
            icon: str | None = None,
            device_class: BinarySensorDeviceClass | None = None,
    ) -> None:
        self._attr_name = sensor_name
        self._attr_icon = icon
        self._getter = getter
        self._attr_device_class = device_class
        super().__init__(coordinator, config_entry, key)

    @property
    def is_on(self) -> bool | None:
        try:
            return self._getter(self.coordinator.data)
        except (TypeError, KeyError, AttributeError):
            return None
