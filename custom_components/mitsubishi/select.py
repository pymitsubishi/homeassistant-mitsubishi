"""Select platform for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_EXPERIMENTAL_FEATURES,
    CONF_EXTERNAL_TEMP_ENTITY,
    DOMAIN,
    TEMP_SOURCE_INTERNAL,
    TEMP_SOURCE_REMOTE,
)
from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi select entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SelectEntity] = [MitsubishiPowerSavingSelect(coordinator, config_entry)]

    # Only add Temperature Source selector if experimental features are enabled
    if config_entry.options.get(CONF_EXPERIMENTAL_FEATURES, False):
        entities.append(MitsubishiTemperatureSourceSelect(coordinator, config_entry))

    async_add_entities(entities)


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


class MitsubishiTemperatureSourceSelect(MitsubishiEntity, SelectEntity):
    """Temperature source mode select for Mitsubishi AC."""

    _attr_name = "Temperature Source"
    _attr_icon = "mdi:thermometer"
    _attr_options = [TEMP_SOURCE_INTERNAL, TEMP_SOURCE_REMOTE]

    def __init__(
        self,
        coordinator: MitsubishiDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the temperature source select."""
        super().__init__(coordinator, config_entry, "temperature_source_select")
        self._config_entry = config_entry

    @property
    def current_option(self) -> str | None:
        """Return the current temperature source mode."""
        return TEMP_SOURCE_REMOTE if self.coordinator.remote_temp_mode else TEMP_SOURCE_INTERNAL

    async def async_select_option(self, option: str) -> None:
        """Set the temperature source mode."""
        if option == TEMP_SOURCE_INTERNAL:
            # Switch to internal sensor
            self.coordinator.set_remote_temp_mode(False)
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_current_temperature,
                None,
            )
            _LOGGER.info("Switched to internal temperature sensor")
        else:
            # Switch to remote sensor - check if external entity is configured
            external_entity_id = self._config_entry.options.get(CONF_EXTERNAL_TEMP_ENTITY)
            if not external_entity_id:
                _LOGGER.warning(
                    "Cannot switch to remote mode: No external temperature entity configured. "
                    "Configure one in the integration options first."
                )
                return

            # Check if the entity is available
            state = self.hass.states.get(external_entity_id)
            if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                _LOGGER.warning(
                    "Cannot switch to remote mode: External entity %s is not available",
                    external_entity_id,
                )
                return

            try:
                temp = float(state.state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Cannot switch to remote mode: Invalid temperature value from %s",
                    external_entity_id,
                )
                return

            # Enable remote mode and send the temperature
            self.coordinator.set_remote_temp_mode(True)
            await self.hass.async_add_executor_job(
                self.coordinator.controller.set_current_temperature,
                temp,
            )
            _LOGGER.info(
                "Switched to remote temperature sensor (%s: %.1f)",
                external_entity_id,
                temp,
            )

        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs: dict[str, Any] = {"source": "Mitsubishi AC"}
        external_entity_id = self._config_entry.options.get(CONF_EXTERNAL_TEMP_ENTITY)
        if external_entity_id:
            attrs["external_temperature_entity"] = external_entity_id
            # Get current value from external entity
            state = self.hass.states.get(external_entity_id)
            if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                try:
                    attrs["external_temperature"] = float(state.state)
                except (ValueError, TypeError):
                    attrs["external_temperature"] = None
        return attrs
