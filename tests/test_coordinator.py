"""Tests for the MitsubishiDataUpdateCoordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mitsubishi.const import (
    CONF_EXPERIMENTAL_FEATURES,
    CONF_EXTERNAL_TEMP_ENTITY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.mitsubishi.coordinator import MitsubishiDataUpdateCoordinator


@pytest.mark.asyncio
async def test_coordinator_init(hass, mock_mitsubishi_controller, mock_config_entry):
    """Test coordinator initialization."""
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry, DEFAULT_SCAN_INTERVAL
    )

    assert coordinator.controller == mock_mitsubishi_controller
    assert coordinator.unit_info is None
    assert coordinator.name == DOMAIN
    assert coordinator.update_interval == timedelta(seconds=DEFAULT_SCAN_INTERVAL)


@pytest.mark.asyncio
async def test_coordinator_init_custom_interval(
    hass, mock_mitsubishi_controller, mock_config_entry
):
    """Test coordinator initialization with custom scan interval."""
    custom_interval = 60
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry, custom_interval
    )

    assert coordinator.update_interval == timedelta(seconds=custom_interval)


@pytest.mark.asyncio
async def test_fetch_unit_info_success(hass, mock_mitsubishi_controller, mock_config_entry):
    """Test successful unit info fetching."""
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry
    )

    # Mock unit info fetch
    expected_unit_info = {"Adapter Information": {"Adaptor name": "MAC-577IF-2E"}}
    mock_mitsubishi_controller.get_unit_info.return_value = expected_unit_info

    result = await coordinator.get_unit_info()

    assert result == expected_unit_info


@pytest.mark.asyncio
async def test_async_update_data_success(hass, mock_mitsubishi_controller, mock_config_entry):
    """Test successful data update."""
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry
    )

    with patch.object(
        hass,
        "async_add_executor_job",
        AsyncMock(return_value=mock_mitsubishi_controller.state),
    ) as mock_executor:
        result = await coordinator._async_update_data()

        mock_executor.assert_called_once_with(mock_mitsubishi_controller.fetch_status)
        assert result == mock_mitsubishi_controller.state


@pytest.mark.asyncio
async def test_async_update_data_fetch_status_fails(
    hass, mock_mitsubishi_controller, mock_config_entry
):
    """Test data update when fetch_status fails."""
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry
    )

    mock_mitsubishi_controller.fetch_status.side_effect = UpdateFailed("foobar")

    with pytest.raises(UpdateFailed, match="foobar"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_remote_temp_mode_property(
    hass, mock_mitsubishi_controller, mock_config_entry
):
    """Test remote_temp_mode property returns False by default."""
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry
    )

    assert coordinator.remote_temp_mode is False


@pytest.mark.asyncio
async def test_coordinator_experimental_features_disabled(
    hass, mock_mitsubishi_controller, mock_config_entry
):
    """Test experimental_features_enabled property when disabled."""
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry
    )

    assert coordinator.experimental_features_enabled is False


@pytest.mark.asyncio
async def test_coordinator_set_remote_temp_mode(
    hass, mock_mitsubishi_controller, mock_config_entry
):
    """Test set_remote_temp_mode method."""
    mock_config_entry.add_to_hass(hass)
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry
    )

    # Enable remote mode (no hardware call when enabling)
    await coordinator.set_remote_temp_mode(True)
    assert coordinator.remote_temp_mode is True

    # Disable remote mode (should call set_current_temperature(None))
    await coordinator.set_remote_temp_mode(False)
    assert coordinator.remote_temp_mode is False
    mock_mitsubishi_controller.set_current_temperature.assert_called_with(None)


@pytest.fixture
def mock_config_entry_experimental():
    """Create a mock config entry with experimental features enabled."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Mitsubishi AC",
        unique_id="00:11:22:33:44:57",
        data={
            CONF_HOST: "192.168.1.100",
            "encryption_key": "unregistered",
            "admin_username": "admin",
            "admin_password": "password",
            "scan_interval": 30,
        },
        options={
            CONF_EXPERIMENTAL_FEATURES: True,
            CONF_EXTERNAL_TEMP_ENTITY: "sensor.room_temp",
        },
        entry_id="test_entry_exp_coord_id",
    )


@pytest.mark.asyncio
async def test_coordinator_experimental_features_enabled(
    hass, mock_mitsubishi_controller, mock_config_entry_experimental
):
    """Test experimental_features_enabled property when enabled."""
    # Need to add config entry to hass first for options to work
    mock_config_entry_experimental.add_to_hass(hass)

    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry_experimental
    )

    assert coordinator.experimental_features_enabled is True


@pytest.mark.asyncio
async def test_async_update_data_with_experimental_first_update_internal(
    hass, mock_mitsubishi_controller, mock_config_entry_experimental
):
    """Test _async_update_data with experimental features on first update in internal mode."""
    mock_config_entry_experimental.add_to_hass(hass)

    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry_experimental
    )
    # Ensure remote mode is off
    coordinator._remote_temp_mode = False

    with patch.object(
        hass,
        "async_add_executor_job",
        AsyncMock(return_value=mock_mitsubishi_controller.state),
    ):
        result = await coordinator._async_update_data()

        assert result == mock_mitsubishi_controller.state
        assert coordinator._startup_mode_applied is True


@pytest.mark.asyncio
async def test_async_update_data_with_experimental_subsequent_update_remote(
    hass, mock_mitsubishi_controller, mock_config_entry_experimental
):
    """Test _async_update_data with experimental features on subsequent update in remote mode."""
    mock_config_entry_experimental.add_to_hass(hass)

    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry_experimental
    )
    # Simulate first update already done
    coordinator._startup_mode_applied = True
    coordinator._remote_temp_mode = True

    # Set up a mock state for the external entity
    hass.states.async_set("sensor.room_temp", "22.5")

    with patch.object(
        hass,
        "async_add_executor_job",
        AsyncMock(return_value=mock_mitsubishi_controller.state),
    ):
        result = await coordinator._async_update_data()

        assert result == mock_mitsubishi_controller.state


@pytest.mark.asyncio
async def test_send_remote_temperature_no_entity_configured(hass, mock_mitsubishi_controller):
    """Test _send_remote_temperature when no external entity is configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Mitsubishi AC",
        unique_id="00:11:22:33:44:58",
        data={CONF_HOST: "192.168.1.100"},
        options={CONF_EXPERIMENTAL_FEATURES: True},  # No CONF_EXTERNAL_TEMP_ENTITY
        entry_id="test_no_entity_id",
    )
    config_entry.add_to_hass(hass)

    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller, config_entry)
    coordinator._remote_temp_mode = True

    with patch.object(hass, "async_add_executor_job", AsyncMock()) as mock_executor:
        await coordinator._send_remote_temperature()

        # Should call set_current_temperature with None to fall back
        mock_executor.assert_called_once()
        assert coordinator._remote_temp_mode is False  # Should be disabled


@pytest.mark.asyncio
async def test_send_remote_temperature_entity_not_found(
    hass, mock_mitsubishi_controller, mock_config_entry_experimental
):
    """Test _send_remote_temperature when external entity is not found."""
    mock_config_entry_experimental.add_to_hass(hass)

    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry_experimental
    )
    coordinator._remote_temp_mode = True
    # sensor.room_temp is not set in hass.states, so get() returns None

    with patch.object(hass, "async_add_executor_job", AsyncMock()) as mock_executor:
        await coordinator._send_remote_temperature()

        # Should call set_current_temperature with None to fall back
        mock_executor.assert_called_once()
        assert coordinator._remote_temp_mode is False


@pytest.mark.asyncio
async def test_send_remote_temperature_entity_unavailable(
    hass, mock_mitsubishi_controller, mock_config_entry_experimental
):
    """Test _send_remote_temperature when external entity is unavailable."""
    mock_config_entry_experimental.add_to_hass(hass)

    # Set the entity state to unavailable
    hass.states.async_set("sensor.room_temp", STATE_UNAVAILABLE)

    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry_experimental
    )
    coordinator._remote_temp_mode = True

    with patch.object(hass, "async_add_executor_job", AsyncMock()) as mock_executor:
        await coordinator._send_remote_temperature()

        mock_executor.assert_called_once()
        assert coordinator._remote_temp_mode is False


@pytest.mark.asyncio
async def test_send_remote_temperature_entity_unknown(
    hass, mock_mitsubishi_controller, mock_config_entry_experimental
):
    """Test _send_remote_temperature when external entity is unknown."""
    mock_config_entry_experimental.add_to_hass(hass)

    # Set the entity state to unknown
    hass.states.async_set("sensor.room_temp", STATE_UNKNOWN)

    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry_experimental
    )
    coordinator._remote_temp_mode = True

    with patch.object(hass, "async_add_executor_job", AsyncMock()) as mock_executor:
        await coordinator._send_remote_temperature()

        mock_executor.assert_called_once()
        assert coordinator._remote_temp_mode is False


@pytest.mark.asyncio
async def test_send_remote_temperature_invalid_value(
    hass, mock_mitsubishi_controller, mock_config_entry_experimental
):
    """Test _send_remote_temperature when temperature value is invalid."""
    mock_config_entry_experimental.add_to_hass(hass)

    # Set the entity state to an invalid value
    hass.states.async_set("sensor.room_temp", "not_a_number")

    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry_experimental
    )
    coordinator._remote_temp_mode = True

    with patch.object(hass, "async_add_executor_job", AsyncMock()) as mock_executor:
        await coordinator._send_remote_temperature()

        mock_executor.assert_called_once()
        assert coordinator._remote_temp_mode is False


@pytest.mark.asyncio
async def test_send_remote_temperature_success(
    hass, mock_mitsubishi_controller, mock_config_entry_experimental
):
    """Test _send_remote_temperature with valid temperature."""
    mock_config_entry_experimental.add_to_hass(hass)

    # Set a valid temperature state
    hass.states.async_set("sensor.room_temp", "21.5")

    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, mock_config_entry_experimental
    )
    coordinator._remote_temp_mode = True

    with patch.object(hass, "async_add_executor_job", AsyncMock()) as mock_executor:
        await coordinator._send_remote_temperature()

        mock_executor.assert_called_once()
        # Remote mode should remain enabled on success
        assert coordinator._remote_temp_mode is True
