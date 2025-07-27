"""Data update coordinator for the Mitsubishi Air Conditioner integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from pymitsubishi import MitsubishiController

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MitsubishiDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Mitsubishi Air Conditioner."""

    def __init__(self, hass: HomeAssistant, controller: MitsubishiController) -> None:
        """Initialize."""
        self.controller = controller
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        try:
            # Fetch status with capability detection enabled
            success = await self.hass.async_add_executor_job(
                self.controller.fetch_status, False, True  # debug=False, detect_capabilities=True
            )
            
            if not success:
                raise UpdateFailed("Failed to communicate with Mitsubishi Air Conditioner")
            
            # Get the status summary which includes capabilities
            return await self.hass.async_add_executor_job(
                self.controller.get_status_summary
            )
            
        except Exception as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex
