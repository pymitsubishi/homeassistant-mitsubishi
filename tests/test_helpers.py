"""Tests for the Mitsubishi Helper functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

from custom_components.mitsubishi import async_setup_entry, async_unload_entry


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_config_entry, mock_coordinator):
    """Test setting up Mitsubishi integration via config entry."""
    with (
        patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class,
        patch(
            "custom_components.mitsubishi.MitsubishiDataUpdateCoordinator",
            return_value=mock_coordinator,
        ),
        patch("custom_components.mitsubishi.dr.async_get") as mock_device_registry,
        patch.object(hass.config_entries, "async_forward_entry_setups", return_value=None),
    ):
        mock_controller = MagicMock()
        mock_controller.fetch_status = MagicMock(return_value=True)
        mock_controller_class.return_value = mock_controller

        mock_coordinator.get_unit_info = AsyncMock(return_value = {})

        # Mock device registry
        mock_registry = MagicMock()
        mock_registry.async_get_or_create = MagicMock(return_value=MagicMock())
        mock_device_registry.return_value = mock_registry

        assert await async_setup_entry(hass, mock_config_entry) is True

        # Check that device info fetching occurs
        mock_coordinator.get_unit_info.assert_called_once()

        # Check that the refresh is attempted
        mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_unload_entry(hass, mock_config_entry, mock_coordinator):
    """Test unloading of config entry."""
    # Set up the data as if the integration was already loaded
    hass.data = {"mitsubishi": {mock_config_entry.entry_id: mock_coordinator}}

    # Mock the async_unload_platforms method to return True
    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=True
    ) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        mock_unload.assert_awaited_once()
        mock_coordinator.controller.api.close.assert_called_once()
        assert mock_config_entry.entry_id not in hass.data["mitsubishi"]


@pytest.mark.asyncio
async def test_async_setup_entry_with_comprehensive_unit_info(
    hass, mock_config_entry, mock_coordinator
):
    """Test setup with comprehensive unit info to cover sw_versions and hw_info branches."""

    with (
        patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class,
        patch(
            "custom_components.mitsubishi.MitsubishiDataUpdateCoordinator",
            return_value=mock_coordinator,
        ),
        patch("custom_components.mitsubishi.dr.async_get") as mock_device_registry,
        patch.object(hass.config_entries, "async_forward_entry_setups", return_value=None),
    ):
        mock_controller = MagicMock()
        mock_controller.fetch_status = MagicMock(return_value=True)
        mock_controller_class.return_value = mock_controller

        # Mock device registry
        mock_registry = MagicMock()
        mock_device_registry.return_value = mock_registry

        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True

        # Verify device registry was called with comprehensive info
        mock_registry.async_get_or_create.assert_called_once()
        call_kwargs = mock_registry.async_get_or_create.call_args[1]

        # Check that sw_version contains all the version components
        sw_version = call_kwargs["sw_version"]
        assert "App: 33.00" in sw_version
        assert "Rel: 00.06" in sw_version
        assert "CP: 01.08" in sw_version


@pytest.mark.asyncio
async def test_async_setup_entry_connection_failure(hass, mock_config_entry):
    """Test setup when connection to device fails."""
    from homeassistant.exceptions import ConfigEntryNotReady

    with (
        patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class,
    ):
        mock_controller_class.side_effect = requests.exceptions.RequestException("foobar")

        # Should raise ConfigEntryNotReady when connection fails
        with pytest.raises(
            ConfigEntryNotReady, match="foobar"
        ):
            await async_setup_entry(hass, mock_config_entry)
