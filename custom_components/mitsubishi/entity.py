"""Base entity class for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


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
            name=f"Mitsubishi AC {device_mac[-8:]}"
            if device_mac
            else f"Mitsubishi AC ({config_entry.data['host']})",
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

    async def _execute_command_with_refresh(
        self, command_name: str, command_func, *args, **kwargs
    ) -> bool:
        """Execute a device command and refresh coordinator data on success.

        This method implements the correct timing for all pymitsubishi commands:
        1. Send command to device
        2. Wait 2 seconds for device to process
        3. Fetch fresh status from device
        4. Update Home Assistant state

        Args:
            command_name: Human-readable name of the command for logging
            command_func: The controller method to execute
            *args, **kwargs: Arguments to pass to the command function

        Returns:
            bool: True if command was successful, False otherwise
        """
        try:
            _LOGGER.info(f"🔧 Executing command: {command_name}")

            # Add debug=True for controller methods that support it
            if "debug" not in kwargs:
                kwargs["debug"] = True

            success = await self.hass.async_add_executor_job(lambda: command_func(*args, **kwargs))

            if success:
                _LOGGER.info(f"✅ Command '{command_name}' sent successfully")

                # Based on timing tests, the device needs ~1.5-2 seconds to process
                # commands and reflect changes in its status. The command response
                # contains the OLD state, not the new state.

                # Wait for the device to process the command
                _LOGGER.info(f"⏳ Waiting for device to process {command_name}...")
                await asyncio.sleep(2.0)  # Based on empirical testing

                # Now fetch fresh data from the device
                await self.coordinator.async_request_refresh()
                _LOGGER.info(f"📊 Coordinator refreshed after {command_name}")

                return True
            else:
                _LOGGER.warning(f"❌ Failed to execute {command_name}")
                return False

        except Exception as e:
            _LOGGER.error(f"💥 Error executing {command_name}: {e}")
            return False
