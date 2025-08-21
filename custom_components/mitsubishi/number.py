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
    async_add_entities(
        [
            MitsubishiDehumidifierNumber(coordinator, config_entry),
        ]
    )


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
        try:
            return self.coordinator.data.general.dehum_setting
        except AttributeError:
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the dehumidifier level."""
        await self._execute_command_with_refresh(
            f"set dehumidifier level to {value}%",
            self.coordinator.controller.set_dehumidifier,
            int(value),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}
