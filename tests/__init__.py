"""Tests for the Mitsubishi Air Conditioner integration."""

from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mitsubishi.const import DOMAIN

TEST_SYSTEM_DATA = {
    "mac": "00:11:22:33:44:55",
    "serial": "TEST123456",
    "power": "ON",
    "mode": "COOLER",
    "target_temp": 24.0,
    "room_temp": 22.5,
    "capabilities": {},
}

USER_INPUT = {
    CONF_HOST: "192.168.1.100",
    "encryption_key": "unregistered",
    "admin_username": "admin",
    "admin_password": "password",
    "scan_interval": 30,
    "enable_capability_detection": True,
}


def patch_controller(return_value=TEST_SYSTEM_DATA, side_effect=None):
    """Patch the Mitsubishi Controller fetch_status method."""
    return patch(
        "custom_components.mitsubishi.config_flow.MitsubishiController.fetch_status",
        new=AsyncMock(return_value=True, side_effect=side_effect),
    )


def patch_get_status_summary(return_value=TEST_SYSTEM_DATA, side_effect=None):
    """Patch the Mitsubishi Controller get_status_summary method."""
    return patch(
        "custom_components.mitsubishi.config_flow.MitsubishiController.get_status_summary",
        return_value=return_value,
        side_effect=side_effect,
    )


def patch_api_close():
    """Patch the Mitsubishi API close method."""
    return patch(
        "custom_components.mitsubishi.config_flow.MitsubishiAPI.close",
    )


async def add_mock_config(hass: HomeAssistant) -> MockConfigEntry:
    """Create a fake Mitsubishi Config Entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test entry",
        unique_id="00:11:22:33:44:55",
        data=USER_INPUT,
    )

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
