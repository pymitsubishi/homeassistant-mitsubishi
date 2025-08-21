"""The Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging

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
            device_host_port=host,
            encryption_key=encryption_key,
            admin_username=admin_username,
            admin_password=admin_password,
        )
        controller = MitsubishiController(api=api)

        # Test connection and raise ConfigEntryNotReady if it fails
        try:
            await hass.async_add_executor_job(controller.fetch_status)
        except Exception as e:
            raise ConfigEntryNotReady(f"Unable to connect to Mitsubishi AC at {host}") from e

        # Create data update coordinator with custom scan interval
        coordinator = MitsubishiDataUpdateCoordinator(hass, controller, scan_interval)

        # Fetch unit info for device registry enrichment
        unit_info = await coordinator.get_unit_info()

        # Fetch initial data
        await coordinator.async_config_entry_first_refresh()

        # Get device information from coordinator data and unit info
        device_mac = unit_info.get("Adaptor Information", {}).get("MAC address")
        device_serial = unit_info.get("Adaptor Information", {}).get("ID")
        device_model = unit_info.get("Adaptor Information", {}).get("Adaptor name")

        sw_versions = []
        if (ver := unit_info.get("Adaptor Information", {}).get("Application version")) is not None:
            sw_versions.append(f"App: {ver}")
        if (ver := unit_info.get("Adaptor Information", {}).get("Release version")) is not None:
            sw_versions.append(f"Rel: {ver}")
        if (ver := unit_info.get("Adaptor Information", {}).get("Flash version")) is not None:
            sw_versions.append(f"Flash: {ver}")
        if (ver := unit_info.get("Adaptor Information", {}).get("Boot version")) is not None:
            sw_versions.append(f"Boot: {ver}")
        if (ver := unit_info.get("Adaptor Information", {}).get("Common platform version")) is not None:
            sw_versions.append(f"CP: {ver}")
        if (ver := unit_info.get("Adaptor Information", {}).get("Test release version")) is not None:
            sw_versions.append(f"Test: {ver}")
        sw_version_str = " | ".join(sw_versions)

        # Register device in device registry with comprehensive info
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device_mac or host)},
            manufacturer="Mitsubishi Electric",
            model=device_model,
            name=f"Mitsubishi AC {device_mac[-8:]}" if device_mac else f"Mitsubishi AC ({host})",
            sw_version=sw_version_str,
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


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating configuration from version %s.%s", config_entry.version, config_entry.minor_version)

    if config_entry.version > 1:
        # downgrade not supported
        return False

    if config_entry.version == 1:
        if config_entry.minor_version > 1:
            # downgrade not supported
            return False
        if config_entry.minor_version == 1:
            return True

        new_data = {**config_entry.data}
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=1, minor_version=1)

    return False
