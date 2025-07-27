"""Base entity class for Mitsubishi Air Conditioner integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator


class MitsubishiEntity(CoordinatorEntity[MitsubishiDataUpdateCoordinator]):
    """Base class for Mitsubishi entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._key = key

        # Get device information (handle case where coordinator.data is None)
        if coordinator.data:
            device_mac = coordinator.data.get("mac", config_entry.data["host"])
            device_serial = coordinator.data.get("serial")
            capabilities = coordinator.data.get("capabilities", {})
        else:
            device_mac = config_entry.data["host"]
            device_serial = None
            capabilities = {}

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_mac)},
            manufacturer="Mitsubishi Electric",
            model=capabilities.get("device_model", "MAC-577IF-2E WiFi Adapter"),
            name=f"Mitsubishi AC {device_mac[-8:]}" if device_mac else f"Mitsubishi AC ({config_entry.data['host']})",
            sw_version=capabilities.get("firmware_version"),
            hw_version=device_mac,
            serial_number=device_serial,
            configuration_url=f"http://{config_entry.data['host']}",
        )

        # Set unique ID
        self._attr_unique_id = f"{device_mac}_{key}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
