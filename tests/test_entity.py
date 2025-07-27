"""Tests for the MobileEntity class."""
import pytest
from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntry

from custom_components.mitsubishi.entity import MitsubishiEntity
from custom_components.mitsubishi.const import DOMAIN
from custom_components.mitsubishi.coordinator import MitsubishiDataUpdateCoordinator

@pytest.mark.asyncio
async def test_mitsubishi_entity_initialization(hass):
    """Test the initialization of MitsubishiEntity."""
    # Setup mock data
    config_data = {
        "host": "192.168.1.100"
    }

    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.data = config_data

    mock_coordinator = MagicMock()
    mock_coordinator.data = {
        "mac": "00:11:22:33:44:55",
        "serial": "TEST123456",
        "capabilities": {
            "device_model": "MAC-577IF-2E",
            "firmware_version": "1.0.0"
        }
    }

    # Create the entity
    entity = MitsubishiEntity(mock_coordinator, mock_config_entry, "test_key")

    # Assert properties are set
    assert entity._config_entry == mock_config_entry
    assert entity._key == "test_key"

    # Check device info attributes
    assert entity.device_info["identifiers"] == {(DOMAIN, "00:11:22:33:44:55")}
    assert entity.device_info["manufacturer"] == "Mitsubishi Electric"
    assert entity.device_info["model"] == "MAC-577IF-2E"
    assert entity.device_info["name"] == "Mitsubishi AC 33:44:55"
    assert entity.device_info["sw_version"] == "1.0.0"
    assert entity.device_info["hw_version"] == "00:11:22:33:44:55"
    assert entity.device_info["serial_number"] == "TEST123456"

    # Check unique ID
    assert entity.unique_id == "00:11:22:33:44:55_test_key"


@pytest.mark.asyncio
async def test_mitsubishi_entity_availability(hass):
    """Test the availability of MitsubishiEntity."""
    # Setup mock data
    config_data = {
        "host": "192.168.1.100"
    }

    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.data = config_data

    mock_coordinator = MagicMock()
    mock_coordinator.data = {}
    mock_coordinator.last_update_success = True

    # Create the entity
    entity = MitsubishiEntity(mock_coordinator, mock_config_entry, "test_key")

    # Check availability
    assert entity.available is True

    # Simulate update failure
    mock_coordinator.last_update_success = False

    # Check availability after failure
    assert entity.available is False


@pytest.mark.asyncio
async def test_mitsubishi_entity_initialization_with_none_data(hass):
    """Test entity initialization when coordinator data is None."""
    # Setup mock data
    config_data = {
        "host": "192.168.1.100"
    }

    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.data = config_data

    mock_coordinator = MagicMock()
    mock_coordinator.data = None  # Simulate initial state
    mock_coordinator.last_update_success = False

    # Should not raise an exception
    entity = MitsubishiEntity(mock_coordinator, mock_config_entry, "test_key")

    # Check that entity was created successfully
    assert entity._config_entry == mock_config_entry
    assert entity._key == "test_key"
    
    # Should have device info based on host fallback
    assert entity.device_info["identifiers"] == {(DOMAIN, "192.168.1.100")}
    assert entity.device_info["manufacturer"] == "Mitsubishi Electric"
    assert entity.device_info["model"] == "MAC-577IF-2E WiFi Adapter"  # Default value
    assert entity.device_info["name"] == "Mitsubishi AC 68.1.100"  # Last 8 chars of IP
    assert entity.device_info["hw_version"] == "192.168.1.100"
    assert entity.device_info["serial_number"] is None
    
    # Check unique ID
    assert entity.unique_id == "192.168.1.100_test_key"
    
    # Check availability
    assert entity.available is False
