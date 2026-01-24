"""Data update coordinator for the Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pymitsubishi import MitsubishiController, ParsedDeviceState

from .const import (
    CONF_EXPERIMENTAL_FEATURES,
    CONF_EXTERNAL_TEMP_ENTITY,
    CONF_REMOTE_TEMP_MODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MitsubishiDataUpdateCoordinator(DataUpdateCoordinator[ParsedDeviceState]):
    """Class to manage fetching data from the Mitsubishi Air Conditioner."""

    def __init__(
        self,
        hass: HomeAssistant,
        controller: MitsubishiController,
        config_entry: ConfigEntry,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize."""
        self.controller = controller
        self.config_entry = config_entry
        self.unit_info = None  # Will be populated on first update or by config flow
        # Load persisted remote temperature mode (AC doesn't report it, so we track it)
        self._remote_temp_mode = config_entry.options.get(CONF_REMOTE_TEMP_MODE, False)
        self._startup_mode_applied = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    def set_remote_temp_mode(self, enabled: bool) -> None:
        """Set whether remote temperature mode is enabled and persist to storage."""
        self._remote_temp_mode = enabled
        _LOGGER.info("Remote temperature mode set to: %s", enabled)

        # Persist to config entry options
        if self.config_entry is not None:
            new_options = dict(self.config_entry.options)
            new_options[CONF_REMOTE_TEMP_MODE] = enabled
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                options=new_options,
            )

    @property
    def remote_temp_mode(self) -> bool:
        """Return whether remote temperature mode is enabled."""
        return self._remote_temp_mode

    @property
    def experimental_features_enabled(self) -> bool:
        """Return whether experimental features are enabled."""
        if self.config_entry is None:
            return False
        return self.config_entry.options.get(CONF_EXPERIMENTAL_FEATURES, False)

    async def get_unit_info(self) -> dict:
        """Fetch unit information once for device info."""
        unit_info = await self.hass.async_add_executor_job(self.controller.get_unit_info)
        return unit_info

    async def _async_update_data(self) -> ParsedDeviceState:
        """Update data via library."""
        _LOGGER.debug("Coordinator fetching device status")

        # Only process remote temperature if experimental features are enabled
        if self.experimental_features_enabled:
            # On first update after startup, restore the persisted mode to the AC
            if not self._startup_mode_applied:
                self._startup_mode_applied = True
                if self._remote_temp_mode:
                    _LOGGER.info("Restoring remote temperature mode from persisted state")
                    await self._send_remote_temperature()
                else:
                    _LOGGER.debug("Starting with internal temperature mode")
            elif self._remote_temp_mode:
                # Regular update - send remote temperature if enabled
                await self._send_remote_temperature()
        else:
            self._startup_mode_applied = True

        # Fetch status from device
        state = await self.hass.async_add_executor_job(
            self.controller.fetch_status,
        )
        return state

    async def _send_remote_temperature(self) -> None:
        """Send remote temperature to AC if configured and available."""
        if self.config_entry is None:
            return
        external_entity_id = self.config_entry.options.get(CONF_EXTERNAL_TEMP_ENTITY)

        if not external_entity_id:
            _LOGGER.warning(
                "Remote temperature mode enabled but no external entity configured, "
                "falling back to internal sensor"
            )
            await self.hass.async_add_executor_job(self.controller.set_current_temperature, None)
            self._remote_temp_mode = False
            return

        state = self.hass.states.get(external_entity_id)

        if state is None:
            _LOGGER.warning(
                "External temperature entity %s not found, falling back to internal sensor",
                external_entity_id,
            )
            await self.hass.async_add_executor_job(self.controller.set_current_temperature, None)
            self._remote_temp_mode = False
            return

        if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            _LOGGER.warning(
                "External temperature entity %s is %s, falling back to internal sensor",
                external_entity_id,
                state.state,
            )
            await self.hass.async_add_executor_job(self.controller.set_current_temperature, None)
            self._remote_temp_mode = False
            return

        try:
            temperature = float(state.state)
            _LOGGER.debug(
                "Sending remote temperature %.1f from %s to AC",
                temperature,
                external_entity_id,
            )
            await self.hass.async_add_executor_job(
                self.controller.set_current_temperature, temperature
            )
        except (ValueError, TypeError) as e:
            _LOGGER.error(
                "Invalid temperature value '%s' from %s: %s, falling back to internal sensor",
                state.state,
                external_entity_id,
                e,
            )
            await self.hass.async_add_executor_job(self.controller.set_current_temperature, None)
            self._remote_temp_mode = False
