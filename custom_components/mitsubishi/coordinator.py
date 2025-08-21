"""Data update coordinator for the Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pymitsubishi import MitsubishiController, ParsedDeviceState

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MitsubishiDataUpdateCoordinator(DataUpdateCoordinator[ParsedDeviceState]):
    """Class to manage fetching data from the Mitsubishi Air Conditioner."""

    def __init__(
        self,
        hass: HomeAssistant,
        controller: MitsubishiController,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize."""
        self.controller = controller
        self.unit_info = None  # Will be populated on first update or by config flow

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def get_unit_info(self) -> dict:
        """Fetch unit information once for device info."""
        unit_info = await self.hass.async_add_executor_job(self.controller.get_unit_info)
        return unit_info

    async def _async_update_data(self) -> ParsedDeviceState:
        """Update data via library."""
        _LOGGER.info("Coordinator fetching device status")
        # This invokes a network call, run in executor to avoid blocking
        state = await self.hass.async_add_executor_job(
            self.controller.fetch_status,
        )
        return state
