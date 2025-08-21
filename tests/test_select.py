"""Tests for the select platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.mitsubishi.const import DOMAIN
from custom_components.mitsubishi.select import (
    MitsubishiPowerSavingSelect,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_coordinator, mock_config_entry):
    """Test the setup of Mitsubishi select entities."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], MitsubishiPowerSavingSelect)


@pytest.mark.asyncio
async def test_power_saving_select_init(hass, mock_coordinator, mock_config_entry):
    """Test power saving select entity initialization."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    assert select._attr_name == "Power Saving Mode"
    assert select._attr_icon == "mdi:power-sleep"
    assert select._attr_options == ["Disabled", "Enabled"]
    assert select.unique_id.endswith("_power_saving_select")


@pytest.mark.asyncio
async def test_power_saving_select_current_option_disabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select current option when disabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    assert select.current_option == "Disabled"

    # Test without power saving mode data
    mock_coordinator.data = None
    assert select.current_option is None


@pytest.mark.asyncio
async def test_power_saving_select_async_select_option_enabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select option selection to enabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await select.async_select_option("Enabled")

        # Should call the lambda function wrapping the controller command
        assert mock_executor.call_count == 1
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_power_saving_select_async_select_option_disabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select option selection to disabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await select.async_select_option("Disabled")

        # Should call the lambda function wrapping the controller command
        assert mock_executor.call_count == 1
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_power_saving_select_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select extra state attributes."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    attributes = select.extra_state_attributes
    assert attributes == {"source": "Mitsubishi AC"}
