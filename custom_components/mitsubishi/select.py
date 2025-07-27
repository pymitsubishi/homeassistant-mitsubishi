"""Select platform for Mitsubishi Air Conditioner integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pymitsubishi import (
    HorizontalWindDirection,
    VerticalWindDirection,
)

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity

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

# Mapping for vertical wind direction names to display options
VERTICAL_WIND_NAME_TO_OPTION = {
    "AUTO": "auto",
    "V1": "position_1",
    "V2": "position_2",
    "V3": "position_3",
    "V4": "position_4",
    "V5": "position_5",
    "SWING": "swing",
}

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

# Mapping for horizontal wind direction names to display options
HORIZONTAL_WIND_NAME_TO_OPTION = {
    "AUTO": "auto",
    "L": "left",
    "LS": "left_center",
    "C": "center",
    "RS": "right_center",
    "R": "right",
    "LC": "left_center_swing",
    "CR": "center_right_swing",
    "LR": "left_right_swing",
    "LCR": "all_positions",
    "LCR_S": "swing",
}


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
            MitsubishiPowerSavingSelect(coordinator, config_entry),
        ]
    )


class MitsubishiVerticalVaneSelect(MitsubishiEntity, SelectEntity):
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
        super().__init__(coordinator, config_entry, "vertical_vane_direction")

    @property
    def current_option(self) -> str | None:
        """Return the current vertical vane direction."""
        # Get the right vane direction from coordinator data
        vane_direction = self.coordinator.data.get("vertical_vane_right")
        if vane_direction:
            return VERTICAL_WIND_NAME_TO_OPTION.get(vane_direction, "auto")
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


class MitsubishiHorizontalVaneSelect(MitsubishiEntity, SelectEntity):
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
        super().__init__(coordinator, config_entry, "horizontal_vane_direction")

    @property
    def current_option(self) -> str | None:
        """Return the current horizontal vane direction."""
        # Get the horizontal vane direction from coordinator data
        vane_direction = self.coordinator.data.get("horizontal_vane")
        if vane_direction:
            return HORIZONTAL_WIND_NAME_TO_OPTION.get(vane_direction, "auto")
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
        if self.coordinator.data.get("power_saving_mode"):
            return "Enabled"
        return "Disabled"

    async def async_select_option(self, option: str) -> None:
        """Set the power saving mode."""
        enabled = option == "Enabled"
        await self.hass.async_add_executor_job(
            self.coordinator.controller.set_power_saving, enabled
        )
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {"source": "Mitsubishi AC"}
