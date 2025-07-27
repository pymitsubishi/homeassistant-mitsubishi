"""Number platform for Mitsubishi Air Conditioner integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi number entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        MitsubishiDehumidifierNumber(coordinator, config_entry),
    ])


class MitsubishiDehumidifierNumber(MitsubishiEntity, NumberEntity):
    """Dehumidifier level control for Mitsubishi AC."""

    _attr_name = "Dehumidifier Level"
    _attr_icon = "mdi:water-percent"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the dehumidifier level number entity."""
        super().__init__(coordinator, config_entry, "dehumidifier_control")

    @property
    def native_value(self) -> float | None:
        """Return the current dehumidifier level."""
        if dehumidifier_level := self.coordinator.data.get("dehumidifier_setting"):
            return float(dehumidifier_level)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the dehumidifier level."""
        _LOGGER.debug("Setting dehumidifier level to %s", value)
        
        try:
            # Call the controller method to set dehumidifier level
            success = await self.hass.async_add_executor_job(
                self.coordinator.controller.set_dehumidifier, int(value), False
            )
            
            if success:
                _LOGGER.debug("Successfully set dehumidifier level to %s", value)
                # Trigger a coordinator update to refresh the state
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to set dehumidifier level to %s", value)
                
        except Exception as ex:
            _LOGGER.error("Error setting dehumidifier level: %s", ex)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}
