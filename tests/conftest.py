"""Shared fixtures for Mitsubishi integration tests."""
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST

from custom_components.mitsubishi.const import (
    CONF_ADMIN_PASSWORD,
    CONF_ADMIN_USERNAME,
    CONF_ENABLE_CAPABILITY_DETECTION,
    CONF_ENCRYPTION_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ENCRYPTION_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

# Import Home Assistant test utilities
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.data = {
        CONF_HOST: "192.168.1.100",
        CONF_ENCRYPTION_KEY: DEFAULT_ENCRYPTION_KEY,
        CONF_ADMIN_USERNAME: DEFAULT_ADMIN_USERNAME,
        CONF_ADMIN_PASSWORD: DEFAULT_ADMIN_PASSWORD,
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_ENABLE_CAPABILITY_DETECTION: True,
    }
    mock_entry.entry_id = "test_entry_id"
    mock_entry.title = "Mitsubishi AC (192.168.1.100)"
    mock_entry.domain = DOMAIN
    # Add a mock setup_lock for async_forward_entry_setups
    mock_entry.setup_lock = MagicMock()
    mock_entry.setup_lock.locked.return_value = False
    return mock_entry


@pytest.fixture
def mock_config_entry_minimal():
    """Return a minimal mock config entry with only required fields."""
    return MagicMock(spec=ConfigEntry, data={
        CONF_HOST: "192.168.1.100",
    }, entry_id="test_entry_id")


@pytest.fixture
def mock_mitsubishi_api():
    """Return a mock MitsubishiAPI instance."""
    with patch("custom_components.mitsubishi.MitsubishiAPI") as mock_api_class:
        mock_api = MagicMock()
        mock_api.close = MagicMock()
        mock_api.get_unit_info = MagicMock(return_value={
            'adaptor_info': {
                'model': 'MAC-577IF-2E',
                'app_version': '1.0.0',
                'mac_address': '00:11:22:33:44:55',
                'manufacturing_date': '2023-01-01',
            },
            'unit_info': {
                'type': 'Air Conditioner',
                'it_protocol_version': '1.0',
            }
        })
        mock_api_class.return_value = mock_api
        yield mock_api


@pytest.fixture
def mock_mitsubishi_controller():
    """Return a mock MitsubishiController instance."""
    with patch("custom_components.mitsubishi.MitsubishiController") as mock_controller_class:
        mock_controller = MagicMock()
        mock_controller.fetch_status = MagicMock(return_value=True)
        mock_controller.get_status_summary = MagicMock(return_value={
            'mac': '00:11:22:33:44:55',
            'serial': 'TEST123456',
            'power': 'ON',
            'mode': 'COOLER',
            'target_temp': 24.0,
            'room_temp': 22.5,
        })
        mock_controller.get_unit_info = MagicMock(return_value={
            'adaptor_info': {
                'model': 'MAC-577IF-2E',
                'app_version': '1.0.0',
                'mac_address': '00:11:22:33:44:55',
            },
            'unit_info': {
                'type': 'Air Conditioner',
            }
        })
        mock_controller.api = MagicMock()
        mock_controller.api.close = MagicMock()
        mock_controller_class.return_value = mock_controller
        yield mock_controller


@pytest.fixture
def mock_coordinator():
    """Return a mock data update coordinator."""
    with patch("custom_components.mitsubishi.coordinator.MitsubishiDataUpdateCoordinator") as mock_coord_class:
        mock_coord = MagicMock()
        mock_coord.data = {
            'mac': '00:11:22:33:44:55',
            'serial': 'TEST123456',
            'power': 'ON',
            'capabilities': {},
        }
        mock_coord.unit_info = {
            'adaptor_info': {
                'model': 'MAC-577IF-2E',
                'app_version': '1.0.0',
            },
            'unit_info': {}
        }
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord.fetch_unit_info = AsyncMock()
        mock_coord.controller = MagicMock()
        mock_coord.controller.api = MagicMock()
        mock_coord.controller.api.close = MagicMock()
        mock_coord_class.return_value = mock_coord
        yield mock_coord


@pytest.fixture
def mock_device_registry():
    """Return a mock device registry."""
    with patch("custom_components.mitsubishi.dr.async_get") as mock_dr_get:
        mock_registry = MagicMock()
        mock_registry.async_get_or_create = MagicMock(return_value=MagicMock())
        mock_dr_get.return_value = mock_registry
        yield mock_registry


@pytest.fixture
def sample_unit_info():
    """Return sample unit info data."""
    return {
        'adaptor_info': {
            'model': 'MAC-577IF-2E',
            'app_version': '1.2.3',
            'release_version': '1.2.3-release',
            'flash_version': '1.0.0',
            'boot_version': '1.0.0',
            'platform_version': '1.0.0',
            'mac_address': '00:11:22:33:44:55',
            'device_id': 12345,
            'manufacturing_date': '2023-01-15',
            'current_time': '2024-01-01 12:00:00',
            'wifi_channel': 6,
            'rssi_dbm': -45,
            'rssi_raw': '-45dBm',
            'it_comm_status': 'OK',
            'server_operation': True,
            'server_comm_status': 'Connected',
            'hems_comm_status': 'Disabled',
            'soi_comm_status': 'OK',
            'thermal_timestamp': None,
        },
        'unit_info': {
            'type': 'Air Conditioner',
            'it_protocol_version': '2.1',
            'error_code': 'None',
        }
    }


@pytest.fixture
def sample_status_summary():
    """Return sample status summary data."""
    return {
        'mac': '00:11:22:33:44:55',
        'serial': 'TEST123456',
        'power': 'ON',
        'mode': 'COOLER',
        'target_temp': 24.0,
        'fan_speed': 'AUTO',
        'dehumidifier_setting': 50,
        'power_saving_mode': False,
        'vertical_vane_right': 'AUTO',
        'vertical_vane_left': 'AUTO',
        'horizontal_vane': 'AUTO',
        'room_temp': 22.5,
        'outside_temp': 18.0,
        'error_code': None,
        'abnormal_state': False,
        'capabilities': {}
    }


# Common test utility fixtures and helpers

@pytest.fixture
def mock_async_methods():
    """Context manager that patches common async methods used in entity tests."""
    @contextmanager
    def _patch_async_methods(hass, coordinator):
        with patch.object(coordinator, 'async_request_refresh', new=AsyncMock()) as mock_refresh, \
             patch.object(hass, 'async_add_executor_job', new=AsyncMock()) as mock_executor:
            yield mock_executor, mock_refresh
    return _patch_async_methods


@pytest.fixture
def setup_entity_with_hass():
    """Helper to set up entity with hass instance."""
    def _setup_entity_with_hass(entity, hass):
        """Set hass attribute on entity for testing."""
        entity.hass = hass
        return entity
    return _setup_entity_with_hass


@pytest.fixture
def update_coordinator_data():
    """Helper to update coordinator data in tests."""
    def _update_coordinator_data(coordinator, data_updates):
        """Update coordinator data with new values."""
        coordinator.data.update(data_updates)
        return coordinator
    return _update_coordinator_data


@pytest.fixture
def create_entity_with_setup():
    """Helper to create and setup entity with common test patterns."""
    def _create_entity_with_setup(entity_class, coordinator, config_entry, hass=None, data_updates=None):
        """Create entity instance with optional hass setup and data updates."""
        entity = entity_class(coordinator, config_entry)

        if data_updates:
            coordinator.data.update(data_updates)

        if hass:
            entity.hass = hass

        return entity
    return _create_entity_with_setup
