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

    async def fetch_unit_info(self) -> dict | None:
        """Fetch unit information once for device info."""
        try:
            if hasattr(self.controller, "get_unit_info"):
                unit_info = await self.hass.async_add_executor_job(self.controller.get_unit_info)
                self.unit_info = unit_info
                return unit_info
            else:
                _LOGGER.warning(
                    "Controller does not support get_unit_info - using pymitsubishi < 0.1.6"
                )
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

            # Fetch status with capability detection enabled and debug logging
            _LOGGER.info("Coordinator fetching device status with debug enabled")
            success = await self.hass.async_add_executor_job(
                self.controller.fetch_status,
                True,  # debug=True for detailed communication logs
                True,  # detect_capabilities=True
            )

            if not success:
                raise UpdateFailed("Failed to communicate with Mitsubishi Air Conditioner")

            # Get the status summary which includes capabilities
            summary = await self.hass.async_add_executor_job(self.controller.get_status_summary)

            _LOGGER.info(
                f"Coordinator fetch completed, target temp: {summary.get('target_temp')}°C, power: {summary.get('power')}"
            )

            # Also add energy states and other enhanced data if available (requires pymitsubishi >= 0.1.7)
            if (
                self.controller.state
                and hasattr(self.controller.state, "energy")
                and self.controller.state.energy
            ):
                energy_data = {
                    "compressor_frequency": self.controller.state.energy.compressor_frequency,
                    "operating": self.controller.state.energy.operating,
                    "estimated_power_watts": self.controller.state.energy.estimated_power_watts,
                }

                # Add energy consumption values if available
                energy_attrs = [
                    "energy_total_kWh",
                    "energy_total_cooling_kWh",
                    "energy_total_heating_kWh",
                    "energy_total_auto_kWh",
                    "energy_total_dry_kWh",
                    "energy_total_fan_kWh",
                ]
                for attr in energy_attrs:
                    if hasattr(self.controller.state.energy, attr):
                        value = getattr(self.controller.state.energy, attr)
                        if value is not None:
                            energy_data[attr] = value

                summary["energy_states"] = energy_data

            # Add enhanced general state data if available (requires pymitsubishi >= 0.1.7)
            if self.controller.state and self.controller.state.general:
                # Check if general state has the enhanced SwiCago fields
                if hasattr(self.controller.state.general, "i_see_sensor"):
                    summary["i_see_sensor_active"] = self.controller.state.general.i_see_sensor
                if hasattr(self.controller.state.general, "mode_raw_value"):
                    summary["mode_raw_value"] = self.controller.state.general.mode_raw_value
                if hasattr(self.controller.state.general, "wide_vane_adjustment"):
                    summary[
                        "wide_vane_adjustment"
                    ] = self.controller.state.general.wide_vane_adjustment
                if hasattr(self.controller.state.general, "temp_mode"):
                    summary["temperature_mode"] = (
                        "direct" if self.controller.state.general.temp_mode else "segment"
                    )

            # Note: Vane direction data is now properly included in status summary with pymitsubishi 0.1.6+

            return summary

        except Exception as ex:
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex
