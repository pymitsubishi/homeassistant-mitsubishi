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
        self.unit_info = None  # Will be populated on first update or by config flow
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def fetch_unit_info(self) -> dict | None:
        """Fetch unit information once for device info."""
        try:
            if hasattr(self.controller, 'get_unit_info'):
                unit_info = await self.hass.async_add_executor_job(
                    self.controller.get_unit_info
                )
                self.unit_info = unit_info
                return unit_info
            else:
                _LOGGER.warning("Controller does not support get_unit_info - using pymitsubishi < 0.1.6")
                return None
        except Exception as ex:
            _LOGGER.warning("Failed to fetch unit info: %s", ex)
            return None

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        try:
            # Fetch unit info on first update if not already done
            if self.unit_info is None:
                await self.fetch_unit_info()
            
            # Fetch status with capability detection enabled
            success = await self.hass.async_add_executor_job(
                self.controller.fetch_status, False, True  # debug=False, detect_capabilities=True
            )
            
            if not success:
                raise UpdateFailed("Failed to communicate with Mitsubishi Air Conditioner")
            
            # Get the status summary which includes capabilities
            summary = await self.hass.async_add_executor_job(
                self.controller.get_status_summary
            )
            
            # Temporarily add vane direction data until pymitsubishi 0.1.5 is available
            # TODO: Remove this when 0.1.5 is published and requirement is updated
            if 'vertical_vane_right' not in summary and hasattr(self.controller.state, 'general') and self.controller.state.general:
                summary['vertical_vane_right'] = self.controller.state.general.vertical_wind_direction_right.name
                summary['vertical_vane_left'] = self.controller.state.general.vertical_wind_direction_left.name
                summary['horizontal_vane'] = self.controller.state.general.horizontal_wind_direction.name
            
            return summary
            
        except Exception as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex
