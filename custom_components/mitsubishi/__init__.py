"""The Mitsubishi Air Conditioner integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from pymitsubishi import MitsubishiAPI, MitsubishiController

from .const import DOMAIN
from .coordinator import MitsubishiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mitsubishi Air Conditioner from a config entry."""
    
    host = entry.data[CONF_HOST]
    
    try:
        # Initialize the API and controller
        api = MitsubishiAPI(device_ip=host)
        controller = MitsubishiController(api=api)
        
        # Test connection
        if not await hass.async_add_executor_job(controller.fetch_status):
            raise ConfigEntryNotReady(f"Unable to connect to Mitsubishi AC at {host}")
        
        # Create data update coordinator
        coordinator = MitsubishiDataUpdateCoordinator(hass, controller)
        
        # Fetch initial data
        await coordinator.async_config_entry_first_refresh()
        
        # Store coordinator in hass data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = coordinator
        
        # Forward the setup to platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        return True
        
    except Exception as ex:
        _LOGGER.exception("Failed to set up Mitsubishi Air Conditioner: %s", ex)
        raise ConfigEntryNotReady from ex


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Clean up coordinator and close API connection
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(coordinator.controller.api.close)
    
    return unload_ok
