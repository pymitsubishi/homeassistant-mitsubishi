"""Base entity class for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo, format_mac
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_OPTIMISTIC_UPDATES, DEFAULT_OPTIMISTIC_UPDATES, DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# The AC is eventually consistent: a command can take longer than one refresh
# to show up in its reported state. Keep an optimistic value until the device
# confirms it, but give up after this many refreshes so a command that silently
# never applies cannot pin the UI to a wrong value forever.
OPTIMISTIC_MAX_REFRESHES = 3

# Distinguishes "no optimistic override" from a legitimate override value of None.
_NO_OPTIMISTIC = object()


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
        # Values shown immediately after a command, before the device confirms
        # them via a coordinator refresh. Keyed by property name (getattr(self,
        # key) must return the device-derived value for that property).
        self._optimistic: dict[str, Any] = {}
        # Refreshes seen for each optimistic key while still unconfirmed.
        self._optimistic_age: dict[str, int] = {}
        # Set while reconciling so the getters return the device value, not the
        # optimistic one, letting us compare the two.
        self._bypass_optimistic = False

        if coordinator.data:
            device_mac = coordinator.data.mac
            device_serial = coordinator.data.serial
        else:
            device_mac = config_entry.data["host"]
            device_serial = None

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_mac)},
            manufacturer="Mitsubishi Electric",
            name=f"Mitsubishi AC {device_mac[-8:]}"
            if device_mac
            else f"Mitsubishi AC ({config_entry.data['host']})",
            hw_version=device_mac,
            serial_number=device_serial,
            connections={(CONNECTION_NETWORK_MAC, format_mac(device_mac))} if device_serial else set(),
            configuration_url=f"http://{config_entry.data['host']}",
        )

        # Set unique ID
        self._attr_unique_id = f"{device_mac}_{key}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def _optimistic_enabled(self) -> bool:
        """Whether optimistic UI updates are enabled for this config entry."""
        return self._config_entry.options.get(CONF_OPTIMISTIC_UPDATES, DEFAULT_OPTIMISTIC_UPDATES)

    def _set_optimistic(self, **values: Any) -> None:
        """Show requested values immediately, until the device confirms them."""
        if not self._optimistic_enabled:
            return
        self._optimistic.update(values)
        for key in values:
            self._optimistic_age[key] = 0
        self.async_write_ha_state()

    def _optimistic_value(self, key: str) -> Any:
        """Return the optimistic override for a property, or a sentinel if none.

        Getters call this so a pending value takes precedence over stale device
        data, except while reconciling (so we can read the device value itself).
        """
        if not self._bypass_optimistic and key in self._optimistic:
            return self._optimistic[key]
        return _NO_OPTIMISTIC

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Drop optimistic values the device now confirms; keep the rest so a
        # slow-to-apply change doesn't briefly snap back to its old value.
        if self._optimistic:
            self._bypass_optimistic = True
            try:
                for key in list(self._optimistic):
                    if getattr(self, key) == self._optimistic[key]:
                        self._clear_optimistic(key)
                    else:
                        self._optimistic_age[key] += 1
                        if self._optimistic_age[key] >= OPTIMISTIC_MAX_REFRESHES:
                            self._clear_optimistic(key)
            finally:
                self._bypass_optimistic = False
        self.async_write_ha_state()

    def _clear_optimistic(self, key: str) -> None:
        """Forget one optimistic override."""
        self._optimistic.pop(key, None)
        self._optimistic_age.pop(key, None)

    async def _execute_command_with_refresh(
        self, command_name: str, command_func, *args, **kwargs
    ) -> bool:
        """Execute a device command and refresh coordinator data on success.

        This method implements the correct timing for all pymitsubishi commands:
        1. Send command to device
        2. Wait for device to process
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
            _LOGGER.debug(f"[{self._config_entry.title}] Executing command: {command_name}")

            # Execute the command
            success = await self.hass.async_add_executor_job(lambda: command_func(*args, **kwargs))

            if success:
                _LOGGER.debug(
                    f"[{self._config_entry.title}] Command '{command_name}' sent successfully"
                )

                # Based on timing tests, the device needs ~1.5-2 seconds to process
                # commands and reflect changes in its status. The command response
                # contains the OLD state, not the new state.

                # Wait for the device to process the command
                _LOGGER.debug(
                    f"[{self._config_entry.title}] Waiting for device to process {command_name}..."
                )
                await asyncio.sleep(self.coordinator.controller.wait_time_after_command)

                # Now fetch fresh data from the device
                await self.coordinator.async_request_refresh()
                _LOGGER.debug(
                    f"[{self._config_entry.title}] Coordinator refreshed after {command_name}"
                )

                return True
            else:
                _LOGGER.warning(f"[{self._config_entry.title}] Failed to execute {command_name}")
                self._revert_optimistic()
                return False

        except Exception as e:
            _LOGGER.error(f"[{self._config_entry.title}] Error executing {command_name}: {e}")
            self._revert_optimistic()
            return False

    def _revert_optimistic(self) -> None:
        """Drop optimistic values after a failed command so the UI snaps back."""
        if self._optimistic:
            self._optimistic.clear()
            self._optimistic_age.clear()
            self.async_write_ha_state()
