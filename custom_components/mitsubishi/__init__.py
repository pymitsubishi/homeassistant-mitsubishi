"""The Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from pymitsubishi import MitsubishiAPI, MitsubishiController

from .const import (
    CONF_ADMIN_PASSWORD,
    CONF_ADMIN_USERNAME,
    CONF_ENCRYPTION_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ENCRYPTION_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import MitsubishiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mitsubishi Air Conditioner from a config entry."""

    host = entry.data[CONF_HOST]
    encryption_key = entry.data.get(CONF_ENCRYPTION_KEY, DEFAULT_ENCRYPTION_KEY)
    admin_username = entry.data.get(CONF_ADMIN_USERNAME, DEFAULT_ADMIN_USERNAME)
    admin_password = entry.data.get(CONF_ADMIN_PASSWORD, DEFAULT_ADMIN_PASSWORD)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    try:
        # Initialize the API and controller with admin credentials
        api = MitsubishiAPI(
            device_ip=host,
            encryption_key=encryption_key,
            admin_username=admin_username,
            admin_password=admin_password,
        )
        controller = MitsubishiController(api=api)

        # Test connection and raise ConfigEntryNotReady if it fails
        if not await hass.async_add_executor_job(controller.fetch_status):
            raise ConfigEntryNotReady(f"Unable to connect to Mitsubishi AC at {host}")

        # Create data update coordinator with custom scan interval
        coordinator = MitsubishiDataUpdateCoordinator(hass, controller, scan_interval)

        # Fetch unit info for device registry enrichment
        await coordinator.fetch_unit_info()

        # Fetch initial data
        await coordinator.async_config_entry_first_refresh()

        # Get device information from coordinator data and unit info
        device_mac = coordinator.data.get("mac", host)
        device_serial = coordinator.data.get("serial")
        capabilities = coordinator.data.get("capabilities", {})
        unit_info: dict[str, Any] = coordinator.unit_info or {}

        # Extract enriched device information from unit info
        adaptor_info = unit_info.get("adaptor_info", {})
        unit_type_info = unit_info.get("unit_info", {})

        # Determine device model from multiple sources
        device_model = (
            adaptor_info.get("model")
            or capabilities.get("device_model")
            or "MAC-577IF-2E WiFi Adapter"
        )

        # Determine firmware version from multiple sources
        firmware_version = adaptor_info.get("app_version") or capabilities.get("firmware_version")

        # Build comprehensive software version string
        sw_versions = []
        if adaptor_info.get("app_version"):
            sw_versions.append(f"App: {adaptor_info['app_version']}")
        if adaptor_info.get("release_version"):
            sw_versions.append(f"Release: {adaptor_info['release_version']}")
        if adaptor_info.get("platform_version"):
            sw_versions.append(f"Platform: {adaptor_info['platform_version']}")
        if unit_type_info.get("it_protocol_version"):
            sw_versions.append(f"Protocol: {unit_type_info['it_protocol_version']}")

        sw_version_str = " | ".join(sw_versions) if sw_versions else firmware_version

        # Build hardware version from manufacturing info
        hw_info = []
        if adaptor_info.get("manufacturing_date"):
            hw_info.append(f"MFG: {adaptor_info['manufacturing_date']}")
        if adaptor_info.get("flash_version"):
            hw_info.append(f"Flash: {adaptor_info['flash_version']}")
        if adaptor_info.get("boot_version"):
            hw_info.append(f"Boot: {adaptor_info['boot_version']}")

        hw_version_str = " | ".join(hw_info) if hw_info else device_mac

        # Register device in device registry with comprehensive info
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device_mac or host)},
            manufacturer="Mitsubishi Electric",
            model=device_model,
            name=f"Mitsubishi AC {device_mac[-8:]}" if device_mac else f"Mitsubishi AC ({host})",
            sw_version=sw_version_str,
            hw_version=hw_version_str,
            serial_number=device_serial,
            suggested_area="Living Room",
            configuration_url=f"http://{host}",
        )

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
