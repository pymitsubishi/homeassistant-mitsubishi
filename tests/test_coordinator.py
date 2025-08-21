"""Tests for the MitsubishiDataUpdateCoordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

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

    # Mock unit info fetch
    expected_unit_info = {"Adapter Information": {"Adaptor name": "MAC-577IF-2E"}}
    mock_mitsubishi_controller.get_unit_info.return_value = expected_unit_info

    result = await coordinator.get_unit_info()

    assert result == expected_unit_info


@pytest.mark.asyncio
async def test_async_update_data_success(hass, mock_mitsubishi_controller):
    """Test successful data update."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    with patch.object(
            hass, "async_add_executor_job",
            AsyncMock(return_value=mock_mitsubishi_controller.state),
    ) as mock_executor:
        result = await coordinator._async_update_data()

        mock_executor.assert_called_once_with(mock_mitsubishi_controller.fetch_status)
        assert result == mock_mitsubishi_controller.state


@pytest.mark.asyncio
async def test_async_update_data_fetch_status_fails(hass, mock_mitsubishi_controller):
    """Test data update when fetch_status fails."""
    coordinator = MitsubishiDataUpdateCoordinator(hass, mock_mitsubishi_controller)

    mock_mitsubishi_controller.fetch_status.side_effect = UpdateFailed("foobar")

    with pytest.raises(UpdateFailed, match="foobar"):
        await coordinator._async_update_data()
