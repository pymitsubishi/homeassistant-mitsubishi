"""Switch platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    """Set up Mitsubishi switches."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([MitsubishiCloudConnectionSwitch(coordinator, config_entry)])


class MitsubishiCloudConnectionSwitch(MitsubishiEntity, SwitchEntity):
    """Controls whether the adapter connects to the MELCloud servers.

    Turning this off keeps the air conditioner fully usable over the local
    network. It only stops the adapter from talking to the manufacturer's
    cloud service.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:cloud-outline"

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, config_entry, "cloud_connection")
        self._attr_name = "MELCloud connection"

    @property
    def available(self) -> bool:
        """Return if the adapter reported its cloud connection setting."""
        return super().available and self.coordinator.data.cloud_connect is not None

    @property
    def is_on(self) -> bool | None:
        """Return whether the adapter connects to the MELCloud servers."""
        return self.coordinator.data.cloud_connect

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Let the adapter connect to the MELCloud servers."""
        await self._execute_command_with_refresh(
            "enable MELCloud connection",
            self.coordinator.controller.set_cloud_connect,
            True,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the adapter from connecting to the MELCloud servers."""
        await self._execute_command_with_refresh(
            "disable MELCloud connection",
            self.coordinator.controller.set_cloud_connect,
            False,
        )
