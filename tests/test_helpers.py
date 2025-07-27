"""Tests for the Mitsubishi Helper functions."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.mitsubishi import async_setup_entry, async_unload_entry


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_config_entry, mock_coordinator):
    """Test setting up Mitsubishi integration via config entry."""
    with patch("custom_components.mitsubishi.MitsubishiAPI") as mock_api_class, \
         patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class, \
         patch("custom_components.mitsubishi.MitsubishiDataUpdateCoordinator", return_value=mock_coordinator), \
         patch("custom_components.mitsubishi.dr.async_get") as mock_device_registry, \
         patch.object(hass.config_entries, 'async_forward_entry_setups', return_value=None):

        # Mock the API and Controller to prevent real network calls
        mock_api = MagicMock()
        mock_api.close = AsyncMock()
        mock_api_class.return_value = mock_api

        mock_controller = MagicMock()
        mock_controller.fetch_status = MagicMock(return_value=True)
        mock_controller_class.return_value = mock_controller

        # Mock device registry
        mock_registry = MagicMock()
        mock_registry.async_get_or_create = MagicMock(return_value=MagicMock())
        mock_device_registry.return_value = mock_registry

        assert await async_setup_entry(hass, mock_config_entry) is True

        # Check that device info fetching occurs
        mock_coordinator.fetch_unit_info.assert_awaited_once()

        # Check that the refresh is attempted
        mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_unload_entry(hass, mock_config_entry, mock_coordinator):
    """Test unloading of config entry."""
    # Set up the data as if the integration was already loaded
    hass.data = {"mitsubishi": {mock_config_entry.entry_id: mock_coordinator}}

    # Mock the async_unload_platforms method to return True
    with patch.object(hass.config_entries, 'async_unload_platforms', return_value=True) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        mock_unload.assert_awaited_once()
        mock_coordinator.controller.api.close.assert_called_once()
        assert mock_config_entry.entry_id not in hass.data["mitsubishi"]


@pytest.mark.asyncio
async def test_async_setup_entry_with_comprehensive_unit_info(hass, mock_config_entry, mock_coordinator):
    """Test setup with comprehensive unit info to cover sw_versions and hw_info branches."""
    # Mock comprehensive unit info to trigger all conditional branches
    mock_coordinator.unit_info = {
        "adaptor_info": {
            "model": "MAC-577IF-2E",
            "app_version": "1.2.3",
            "release_version": "1.2.3-release",
            "platform_version": "4.5.6",
            "manufacturing_date": "2023-01-15",
            "flash_version": "2.1.0",
            "boot_version": "1.5.0",
        },
        "unit_info": {
            "it_protocol_version": "2.1"
        }
    }

    mock_coordinator.data = {
        "mac": "00:11:22:33:44:55",
        "serial": "TEST123456",
        "capabilities": {}
    }

    with patch("custom_components.mitsubishi.MitsubishiAPI") as mock_api_class, \
         patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class, \
         patch("custom_components.mitsubishi.MitsubishiDataUpdateCoordinator", return_value=mock_coordinator), \
         patch("custom_components.mitsubishi.dr.async_get") as mock_device_registry, \
         patch.object(hass.config_entries, 'async_forward_entry_setups', return_value=None):

        # Mock the API and Controller to prevent real network calls
        mock_api = MagicMock()
        mock_api.close = AsyncMock()
        mock_api_class.return_value = mock_api

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
        assert "App: 1.2.3" in sw_version
        assert "Release: 1.2.3-release" in sw_version
        assert "Platform: 4.5.6" in sw_version
        assert "Protocol: 2.1" in sw_version

        # Check that hw_version contains all the hardware components
        hw_version = call_kwargs["hw_version"]
        assert "MFG: 2023-01-15" in hw_version
        assert "Flash: 2.1.0" in hw_version
        assert "Boot: 1.5.0" in hw_version


@pytest.mark.asyncio
async def test_async_setup_entry_with_minimal_unit_info(hass, mock_config_entry, mock_coordinator):
    """Test setup with minimal unit info to cover empty sw_versions and hw_info branches."""
    # Mock minimal unit info to test empty branches
    mock_coordinator.unit_info = {
        "adaptor_info": {
            "model": "MAC-577IF-2E",
            # No version info to test empty sw_versions and hw_info
        },
        "unit_info": {
            # No protocol version
        }
    }

    mock_coordinator.data = {
        "mac": "00:11:22:33:44:55",
        "serial": "TEST123456",
        "capabilities": {}
    }

    with patch("custom_components.mitsubishi.MitsubishiAPI") as mock_api_class, \
         patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class, \
         patch("custom_components.mitsubishi.MitsubishiDataUpdateCoordinator", return_value=mock_coordinator), \
         patch("custom_components.mitsubishi.dr.async_get") as mock_device_registry, \
         patch.object(hass.config_entries, 'async_forward_entry_setups', return_value=None):

        # Mock the API and Controller to prevent real network calls
        mock_api = MagicMock()
        mock_api.close = AsyncMock()
        mock_api_class.return_value = mock_api

        mock_controller = MagicMock()
        mock_controller.fetch_status = MagicMock(return_value=True)
        mock_controller_class.return_value = mock_controller

        # Mock device registry
        mock_registry = MagicMock()
        mock_device_registry.return_value = mock_registry

        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True

        # Verify device registry was called
        mock_registry.async_get_or_create.assert_called_once()
        call_kwargs = mock_registry.async_get_or_create.call_args[1]

        # Check that sw_version and hw_version handle missing info correctly
        # sw_version falls back to firmware_version which can be None, then None is passed
        # hw_version falls back to device_mac when hw_info is empty
        assert call_kwargs["sw_version"] is None  # No firmware_version in minimal setup
        assert call_kwargs["hw_version"] == "00:11:22:33:44:55"  # Falls back to device_mac


@pytest.mark.asyncio
async def test_async_setup_entry_partial_unit_info(hass, mock_config_entry, mock_coordinator):
    """Test setup with partial unit info to cover some conditional branches."""
    # Mock partial unit info to test some branches
    mock_coordinator.unit_info = {
        "adaptor_info": {
            "model": "MAC-577IF-2E",
            "app_version": "1.0.0",
            "manufacturing_date": "2023-05-20",
            # Missing other version info
        },
        "unit_info": {
            "it_protocol_version": "1.5"
        }
    }

    mock_coordinator.data = {
        "mac": "00:11:22:33:44:55",
        "serial": "TEST123456",
        "capabilities": {}
    }

    with patch("custom_components.mitsubishi.MitsubishiAPI") as mock_api_class, \
         patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class, \
         patch("custom_components.mitsubishi.MitsubishiDataUpdateCoordinator", return_value=mock_coordinator), \
         patch("custom_components.mitsubishi.dr.async_get") as mock_device_registry, \
         patch.object(hass.config_entries, 'async_forward_entry_setups', return_value=None):

        # Mock the API and Controller to prevent real network calls
        mock_api = MagicMock()
        mock_api.close = AsyncMock()
        mock_api_class.return_value = mock_api

        mock_controller = MagicMock()
        mock_controller.fetch_status = MagicMock(return_value=True)
        mock_controller_class.return_value = mock_controller

        # Mock device registry
        mock_registry = MagicMock()
        mock_device_registry.return_value = mock_registry

        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True

        # Verify device registry was called
        mock_registry.async_get_or_create.assert_called_once()
        call_kwargs = mock_registry.async_get_or_create.call_args[1]

        # Check that sw_version contains only available components
        sw_version = call_kwargs["sw_version"]
        assert "App: 1.0.0" in sw_version
        assert "Protocol: 1.5" in sw_version
        assert "Release:" not in sw_version  # Should not be present
        assert "Platform:" not in sw_version  # Should not be present

        # Check that hw_version contains only available components
        hw_version = call_kwargs["hw_version"]
        assert "MFG: 2023-05-20" in hw_version
        assert "Flash:" not in hw_version  # Should not be present
        assert "Boot:" not in hw_version  # Should not be present


@pytest.mark.asyncio
async def test_async_setup_entry_connection_failure(hass, mock_config_entry):
    """Test setup when connection to device fails."""
    from homeassistant.exceptions import ConfigEntryNotReady

    with patch("custom_components.mitsubishi.MitsubishiAPI") as mock_api_class, \
         patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class:

        # Mock the API and Controller
        mock_api = MagicMock()
        mock_api.close = AsyncMock()
        mock_api_class.return_value = mock_api

        mock_controller = MagicMock()
        mock_controller.fetch_status = MagicMock(return_value=False)  # Connection fails
        mock_controller_class.return_value = mock_controller

        # Should raise ConfigEntryNotReady when connection fails
        with pytest.raises(ConfigEntryNotReady, match="Unable to connect to Mitsubishi AC at 192.168.1.100"):
            await async_setup_entry(hass, mock_config_entry)
