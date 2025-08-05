"""Fixtures for mitsubishi."""

from __future__ import annotations

import pytest

from . import patch_api_close, patch_controller, patch_get_status_summary

# Import Home Assistant test utilities
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def mock_controller():
    """Fixture to patch the Mitsubishi Controller methods."""
    with patch_controller() as mock_controller:
        yield mock_controller


@pytest.fixture
def mock_get_status_summary():
    """Fixture to patch the Mitsubishi Controller status summary method."""
    with patch_get_status_summary() as mock_get_status_summary:
        yield mock_get_status_summary


@pytest.fixture
def mock_api_close():
    """Fixture to patch the Mitsubishi API close method."""
    with patch_api_close() as mock_api_close:
        yield mock_api_close


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    from unittest.mock import AsyncMock, MagicMock

    from custom_components.mitsubishi.const import DOMAIN

    from . import TEST_SYSTEM_DATA

    coordinator = MagicMock()
    coordinator.data = TEST_SYSTEM_DATA
    coordinator.domain = DOMAIN
    coordinator.update_interval = 30
    coordinator.fetch_unit_info = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_update_listeners = MagicMock()

    # Add controller with API mock
    coordinator.controller = MagicMock()
    coordinator.controller.api = MagicMock()
    coordinator.controller.api.close = MagicMock()

    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    from homeassistant.const import CONF_HOST
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.mitsubishi.const import DOMAIN

    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Mitsubishi AC",
        unique_id="00:11:22:33:44:55",
        data={
            CONF_HOST: "192.168.1.100",
            "encryption_key": "unregistered",
            "admin_username": "admin",
            "admin_password": "password",
            "scan_interval": 30,
            "enable_capability_detection": True,
        },
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_mitsubishi_controller():
    """Return a mock MitsubishiController instance."""
    from unittest.mock import MagicMock

    mock_controller = MagicMock()
    mock_controller.fetch_status = MagicMock(return_value=True)
    mock_controller.get_status_summary = MagicMock(
        return_value={
            "mac": "00:11:22:33:44:55",
            "serial": "TEST123456",
            "power": "ON",
            "mode": "COOLER",
            "target_temp": 24.0,
            "room_temp": 22.5,
        }
    )
    mock_controller.get_unit_info = MagicMock(
        return_value={
            "adaptor_info": {
                "model": "MAC-577IF-2E",
                "app_version": "1.0.0",
                "mac_address": "00:11:22:33:44:55",
            },
            "unit_info": {
                "type": "Air Conditioner",
            },
        }
    )
    mock_controller.api = MagicMock()
    mock_controller.api.close = MagicMock()
    return mock_controller


@pytest.fixture
def mock_async_methods():
    """Context manager that patches common async methods used in entity tests."""
    from contextlib import contextmanager
    from unittest.mock import AsyncMock, patch

    @contextmanager
    def _patch_async_methods(hass, coordinator):
        with patch.object(
            coordinator, "async_request_refresh", new=AsyncMock()
        ) as mock_refresh, patch.object(
            hass, "async_add_executor_job", new=AsyncMock()
        ) as mock_executor:
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

    def _create_entity_with_setup(
        entity_class, coordinator, config_entry, hass=None, data_updates=None
    ):
        """Create entity instance with optional hass setup and data updates."""
        entity = entity_class(coordinator, config_entry)

        if data_updates:
            coordinator.data.update(data_updates)

        if hass:
            entity.hass = hass

        return entity

    return _create_entity_with_setup
