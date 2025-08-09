"""Tests for the MitsubishiDataUpdateCoordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.mitsubishi.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from custom_components.mitsubishi.coordinator import MitsubishiDataUpdateCoordinator


@pytest.mark.asyncio
async def test_coordinator_init(hass, mock_mitsubishi_controller):
    """Test coordinator initialization."""
    coordinator = MitsubishiDataUpdateCoordinator(
        hass, mock_mitsubishi_controller, DEFAULT_SCAN_INTERVAL
    )

    assert coordinator.controller == mock_mitsubishi_controller
    assert coordinator.unit_info is None
    assert coordinator.name == DOMAIN
    assert coordinator.update_interval == timedelta(seconds=DEFAULT_SCAN_INTERVAL)


@pytest.mark.asyncio
async def test_coordinator_init_custom_interval(hass, mock_mitsubishi_controller):
    """Test coordinator initialization with custom scan interval."""
    custom_interval = 60
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller, custom_interval)

    assert coordinator.update_interval == timedelta(seconds=custom_interval)


@pytest.mark.asyncio
async def test_fetch_unit_info_success(hass, mock_mitsubishi_controller):
    """Test successful unit info fetching."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    expected_unit_info = {
        "adaptor_info": {"model": "MAC-577IF-2E"},
        "unit_info": {"type": "Air Conditioner"},
    }
    mock_mitsubishi_controller.get_unit_info.return_value = expected_unit_info

    result = await coordinator.fetch_unit_info()

    assert result == expected_unit_info
    assert coordinator.unit_info == expected_unit_info


@pytest.mark.asyncio
async def test_fetch_unit_info_no_method(hass):
    """Test unit info fetching when controller doesn't support get_unit_info."""
    mock_controller = MagicMock()
    # Remove get_unit_info method
    del mock_controller.get_unit_info

    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_controller)

    result = await coordinator.fetch_unit_info()

    assert result is None
    assert coordinator.unit_info is None


@pytest.mark.asyncio
async def test_fetch_unit_info_exception(hass, mock_mitsubishi_controller):
    """Test unit info fetching when an exception occurs."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    mock_mitsubishi_controller.get_unit_info.side_effect = Exception("Network error")

    result = await coordinator.fetch_unit_info()

    assert result is None
    assert coordinator.unit_info is None


@pytest.mark.asyncio
async def test_async_update_data_success(hass, mock_mitsubishi_controller):
    """Test successful data update."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    expected_summary = {
        "power": "ON",
        "mode": "COOLER",
        "target_temp": 24.0,
        "room_temp": 22.5,
    }
    mock_mitsubishi_controller.fetch_status.return_value = True
    mock_mitsubishi_controller.get_status_summary.return_value = expected_summary

    with patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor:
        # Mock the three calls: fetch_unit_info (if needed), fetch_status, get_status_summary
        mock_executor.side_effect = [
            None,
            True,
            expected_summary,
        ]  # unit_info, fetch_status, get_status_summary

        result = await coordinator._async_update_data()

        assert result == expected_summary
        # Verify fetch_status was called with correct parameter (detect_capabilities=True)
        mock_executor.assert_any_call(mock_mitsubishi_controller.fetch_status, True)


@pytest.mark.asyncio
async def test_async_update_data_with_unit_info_fetch(hass, mock_mitsubishi_controller):
    """Test data update that also fetches unit info on first run."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    # Mock unit info fetch
    expected_unit_info = {"adaptor_info": {"model": "MAC-577IF-2E"}}
    mock_mitsubishi_controller.get_unit_info.return_value = expected_unit_info

    expected_summary = {"power": "ON"}
    mock_mitsubishi_controller.fetch_status.return_value = True
    mock_mitsubishi_controller.get_status_summary.return_value = expected_summary

    result = await coordinator._async_update_data()

    assert result == expected_summary
    assert coordinator.unit_info == expected_unit_info


@pytest.mark.asyncio
async def test_async_update_data_with_vane_data(hass, mock_mitsubishi_controller):
    """Test data update with vane direction data (now included by pymitsubishi 0.1.6+)."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    # pymitsubishi 0.1.6+ includes vane data in the status summary
    expected_summary = {
        "power": "ON",
        "vertical_vane_right": "AUTO",
        "vertical_vane_left": "AUTO",
        "horizontal_vane": "AUTO",
    }
    mock_mitsubishi_controller.fetch_status.return_value = True
    mock_mitsubishi_controller.get_status_summary.return_value = expected_summary

    result = await coordinator._async_update_data()

    # Vane data should be present in result (included by pymitsubishi)
    assert result == expected_summary
    assert result["vertical_vane_right"] == "AUTO"
    assert result["vertical_vane_left"] == "AUTO"
    assert result["horizontal_vane"] == "AUTO"


@pytest.mark.asyncio
async def test_async_update_data_fetch_status_fails(hass, mock_mitsubishi_controller):
    """Test data update when fetch_status fails."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    mock_mitsubishi_controller.fetch_status.return_value = False

    with pytest.raises(UpdateFailed, match="Failed to communicate with Mitsubishi Air Conditioner"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_async_update_data_exception(hass, mock_mitsubishi_controller):
    """Test data update when an exception occurs."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    mock_mitsubishi_controller.fetch_status.side_effect = Exception("Network error")

    with pytest.raises(UpdateFailed, match="Error communicating with API: Network error"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_async_update_data_skip_unit_info_if_already_set(hass, mock_mitsubishi_controller):
    """Test that unit info is not fetched again if already set."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    # Pre-set unit info
    coordinator.unit_info = {"existing": "data"}

    expected_summary = {"power": "ON"}
    mock_mitsubishi_controller.fetch_status.return_value = True
    mock_mitsubishi_controller.get_status_summary.return_value = expected_summary

    result = await coordinator._async_update_data()

    assert result == expected_summary
    # get_unit_info should not have been called
    mock_mitsubishi_controller.get_unit_info.assert_not_called()
