"""Select platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi select entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            MitsubishiPowerSavingSelect(coordinator, config_entry),
        ]
    )


class MitsubishiPowerSavingSelect(MitsubishiEntity, SelectEntity):
    """Power saving mode select for Mitsubishi AC."""

    _attr_name = "Power Saving Mode"
    _attr_icon = "mdi:power-sleep"
    _attr_options = ["Disabled", "Enabled"]

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the power saving select."""
        super().__init__(coordinator, config_entry, "power_saving_select")

    @property
    def current_option(self) -> str | None:
        """Return the current power saving mode."""
        try:
            return "Enabled" if self.coordinator.data.general.is_power_saving else "Disabled"
        except AttributeError:
            return None

    async def async_select_option(self, option: str) -> None:
        """Set the power saving mode."""
        enabled = option == "Enabled"
        await self._execute_command_with_refresh(
            f"set power saving mode to {option}",
            self.coordinator.controller.set_power_saving,
            enabled,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}
