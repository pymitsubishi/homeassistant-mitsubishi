"""Select platform for Mitsubishi Air Conditioner integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pymitsubishi import (
    VerticalWindDirection,
    HorizontalWindDirection,
)

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator


# Mapping for vertical wind direction
VERTICAL_WIND_OPTIONS = {
    "auto": VerticalWindDirection.AUTO,
    "position_1": VerticalWindDirection.V1,
    "position_2": VerticalWindDirection.V2,
    "position_3": VerticalWindDirection.V3,
    "position_4": VerticalWindDirection.V4,
    "position_5": VerticalWindDirection.V5,
    "swing": VerticalWindDirection.SWING,
}

VERTICAL_WIND_REVERSE = {v: k for k, v in VERTICAL_WIND_OPTIONS.items()}

# Mapping for horizontal wind direction
HORIZONTAL_WIND_OPTIONS = {
    "auto": HorizontalWindDirection.AUTO,
    "left": HorizontalWindDirection.L,
    "left_center": HorizontalWindDirection.LS,
    "center": HorizontalWindDirection.C,
    "right_center": HorizontalWindDirection.RS,
    "right": HorizontalWindDirection.R,
    "left_center_swing": HorizontalWindDirection.LC,
    "center_right_swing": HorizontalWindDirection.CR,
    "left_right_swing": HorizontalWindDirection.LR,
    "all_positions": HorizontalWindDirection.LCR,
    "swing": HorizontalWindDirection.LCR_S,
}

HORIZONTAL_WIND_REVERSE = {v: k for k, v in HORIZONTAL_WIND_OPTIONS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi select entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            MitsubishiVerticalVaneSelect(coordinator, config_entry),
            MitsubishiHorizontalVaneSelect(coordinator, config_entry),
        ]
    )


class MitsubishiVerticalVaneSelect(
    CoordinatorEntity[MitsubishiDataUpdateCoordinator], SelectEntity
):
    """Vertical vane direction select for Mitsubishi AC."""

    _attr_name = "Vertical Vane Direction"
    _attr_icon = "mdi:arrow-up-down"
    _attr_options = list(VERTICAL_WIND_OPTIONS.keys())

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the vertical vane select."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('mac', config_entry.data['host'])}_vertical_vane"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data.get("mac", config_entry.data["host"]))},
        }

    @property
    def current_option(self) -> str | None:
        """Return the current vertical vane direction."""
        # This would need to be implemented based on the actual state data
        # For now, return a default
        return "auto"

    async def async_select_option(self, option: str) -> None:
        """Set the vertical vane direction."""
        if option in VERTICAL_WIND_OPTIONS:
            direction = VERTICAL_WIND_OPTIONS[option]
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_vertical_vane, direction, "right"
            )
            await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"side": "right"}


class MitsubishiHorizontalVaneSelect(
    CoordinatorEntity[MitsubishiDataUpdateCoordinator], SelectEntity
):
    """Horizontal vane direction select for Mitsubishi AC."""

    _attr_name = "Horizontal Vane Direction"
    _attr_icon = "mdi:arrow-left-right"
    _attr_options = list(HORIZONTAL_WIND_OPTIONS.keys())

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the horizontal vane select."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.data.get('mac', config_entry.data['host'])}_horizontal_vane"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data.get("mac", config_entry.data["host"]))},
        }

    @property
    def current_option(self) -> str | None:
        """Return the current horizontal vane direction."""
        # This would need to be implemented based on the actual state data
        # For now, return a default
        return "auto"

    async def async_select_option(self, option: str) -> None:
        """Set the horizontal vane direction."""
        if option in HORIZONTAL_WIND_OPTIONS:
            direction = HORIZONTAL_WIND_OPTIONS[option]
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_horizontal_vane, direction
            )
            await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"control_type": "horizontal"}
