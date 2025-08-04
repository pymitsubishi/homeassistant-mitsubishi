"""Tests for the select platform."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymitsubishi import HorizontalWindDirection, VerticalWindDirection

from custom_components.mitsubishi.const import DOMAIN
from custom_components.mitsubishi.select import (
    HORIZONTAL_WIND_OPTIONS,
    VERTICAL_WIND_OPTIONS,
    MitsubishiHorizontalVaneSelect,
    MitsubishiPowerSavingSelect,
    MitsubishiVerticalVaneSelect,
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
    assert len(entities) == 3
    assert isinstance(entities[0], MitsubishiVerticalVaneSelect)
    assert isinstance(entities[1], MitsubishiHorizontalVaneSelect)
    assert isinstance(entities[2], MitsubishiPowerSavingSelect)


@pytest.mark.asyncio
async def test_vertical_vane_select_init(hass, mock_coordinator, mock_config_entry):
    """Test vertical vane select entity initialization."""
    select = MitsubishiVerticalVaneSelect(mock_coordinator, mock_config_entry)

    assert select._attr_name == "Vertical Vane Direction"
    assert select._attr_icon == "mdi:arrow-up-down"
    assert select._attr_options == list(VERTICAL_WIND_OPTIONS.keys())
    assert select.unique_id.endswith("_vertical_vane_direction")


@pytest.mark.asyncio
async def test_vertical_vane_select_current_option(hass, mock_coordinator, mock_config_entry):
    """Test vertical vane select current option property."""
    select = MitsubishiVerticalVaneSelect(mock_coordinator, mock_config_entry)

    # Test with known vane direction
    mock_coordinator.data = {"vertical_vane_right": "SWING"}
    assert select.current_option == "swing"

    # Test with unknown vane direction (should default to auto)
    mock_coordinator.data = {"vertical_vane_right": "UNKNOWN"}
    assert select.current_option == "auto"

    # Test without vane direction data
    mock_coordinator.data = {}
    assert select.current_option == "auto"


@pytest.mark.asyncio
async def test_vertical_vane_select_current_option_all_mappings(
    hass, mock_coordinator, mock_config_entry
):
    """Test vertical vane select current option with all possible mappings."""
    select = MitsubishiVerticalVaneSelect(mock_coordinator, mock_config_entry)

    test_cases = [
        ("AUTO", "auto"),
        ("V1", "position_1"),
        ("V2", "position_2"),
        ("V3", "position_3"),
        ("V4", "position_4"),
        ("V5", "position_5"),
        ("SWING", "swing"),
    ]

    for input_val, expected_option in test_cases:
        mock_coordinator.data = {"vertical_vane_right": input_val}
        assert select.current_option == expected_option


@pytest.mark.asyncio
async def test_vertical_vane_select_async_select_option(hass, mock_coordinator, mock_config_entry):
    """Test vertical vane select option selection."""
    select = MitsubishiVerticalVaneSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
        await select.async_select_option("swing")

        # Should call the lambda function wrapping the controller command
        assert mock_executor.call_count == 1
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_vertical_vane_select_async_select_invalid_option(
    hass, mock_coordinator, mock_config_entry
):
    """Test vertical vane select with invalid option."""
    select = MitsubishiVerticalVaneSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with patch.object(hass, "async_add_executor_job") as mock_executor:
        await select.async_select_option("invalid_option")

        # Should not call controller for invalid option
        mock_executor.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_vertical_vane_select_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test vertical vane select extra state attributes."""
    select = MitsubishiVerticalVaneSelect(mock_coordinator, mock_config_entry)

    attributes = select.extra_state_attributes
    assert attributes == {"side": "right"}


@pytest.mark.asyncio
async def test_horizontal_vane_select_init(hass, mock_coordinator, mock_config_entry):
    """Test horizontal vane select entity initialization."""
    select = MitsubishiHorizontalVaneSelect(mock_coordinator, mock_config_entry)

    assert select._attr_name == "Horizontal Vane Direction"
    assert select._attr_icon == "mdi:arrow-left-right"
    assert select._attr_options == list(HORIZONTAL_WIND_OPTIONS.keys())
    assert select.unique_id.endswith("_horizontal_vane_direction")


@pytest.mark.asyncio
async def test_horizontal_vane_select_current_option(hass, mock_coordinator, mock_config_entry):
    """Test horizontal vane select current option property."""
    select = MitsubishiHorizontalVaneSelect(mock_coordinator, mock_config_entry)

    # Test with known vane direction
    mock_coordinator.data = {"horizontal_vane": "LCR_S"}
    assert select.current_option == "swing"

    # Test with unknown vane direction (should default to auto)
    mock_coordinator.data = {"horizontal_vane": "UNKNOWN"}
    assert select.current_option == "auto"

    # Test without vane direction data
    mock_coordinator.data = {}
    assert select.current_option == "auto"


@pytest.mark.asyncio
async def test_horizontal_vane_select_current_option_all_mappings(
    hass, mock_coordinator, mock_config_entry
):
    """Test horizontal vane select current option with all possible mappings."""
    select = MitsubishiHorizontalVaneSelect(mock_coordinator, mock_config_entry)

    test_cases = [
        ("AUTO", "auto"),
        ("L", "left"),
        ("LS", "left_center"),
        ("C", "center"),
        ("RS", "right_center"),
        ("R", "right"),
        ("LC", "left_center_swing"),
        ("CR", "center_right_swing"),
        ("LR", "left_right_swing"),
        ("LCR", "all_positions"),
        ("LCR_S", "swing"),
    ]

    for input_val, expected_option in test_cases:
        mock_coordinator.data = {"horizontal_vane": input_val}
        assert select.current_option == expected_option


@pytest.mark.asyncio
async def test_horizontal_vane_select_async_select_option(
    hass, mock_coordinator, mock_config_entry
):
    """Test horizontal vane select option selection."""
    select = MitsubishiHorizontalVaneSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
        await select.async_select_option("center")

        # Should call the lambda function wrapping the controller command
        assert mock_executor.call_count == 1
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_horizontal_vane_select_async_select_invalid_option(
    hass, mock_coordinator, mock_config_entry
):
    """Test horizontal vane select with invalid option."""
    select = MitsubishiHorizontalVaneSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with patch.object(hass, "async_add_executor_job") as mock_executor:
        await select.async_select_option("invalid_option")

        # Should not call controller for invalid option
        mock_executor.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_horizontal_vane_select_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test horizontal vane select extra state attributes."""
    select = MitsubishiHorizontalVaneSelect(mock_coordinator, mock_config_entry)

    attributes = select.extra_state_attributes
    assert attributes == {"control_type": "horizontal"}


@pytest.mark.asyncio
async def test_power_saving_select_init(hass, mock_coordinator, mock_config_entry):
    """Test power saving select entity initialization."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    assert select._attr_name == "Power Saving Mode"
    assert select._attr_icon == "mdi:power-sleep"
    assert select._attr_options == ["Disabled", "Enabled"]
    assert select.unique_id.endswith("_power_saving_select")


@pytest.mark.asyncio
async def test_power_saving_select_current_option_enabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select current option when enabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    mock_coordinator.data = {"power_saving_mode": True}
    assert select.current_option == "Enabled"


@pytest.mark.asyncio
async def test_power_saving_select_current_option_disabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select current option when disabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    mock_coordinator.data = {"power_saving_mode": False}
    assert select.current_option == "Disabled"

    # Test without power saving mode data
    mock_coordinator.data = {}
    assert select.current_option == "Disabled"


@pytest.mark.asyncio
async def test_power_saving_select_async_select_option_enabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select option selection to enabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
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

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
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


@pytest.mark.asyncio
async def test_vertical_vane_select_all_options(hass, mock_coordinator, mock_config_entry):
    """Test vertical vane select with all valid options."""
    select = MitsubishiVerticalVaneSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    test_cases = [
        ("auto", VerticalWindDirection.AUTO),
        ("position_1", VerticalWindDirection.V1),
        ("position_2", VerticalWindDirection.V2),
        ("position_3", VerticalWindDirection.V3),
        ("position_4", VerticalWindDirection.V4),
        ("position_5", VerticalWindDirection.V5),
        ("swing", VerticalWindDirection.SWING),
    ]

    for option, _ in test_cases:
        with patch.object(
            mock_coordinator, "async_request_refresh", new=AsyncMock()
        ) as mock_refresh, patch.object(
            hass, "async_add_executor_job", new=AsyncMock()
        ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
            await select.async_select_option(option)

            # Should call the lambda function wrapping the controller command
            assert mock_executor.call_count == 1
            mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_horizontal_vane_select_all_options(hass, mock_coordinator, mock_config_entry):
    """Test horizontal vane select with all valid options."""
    select = MitsubishiHorizontalVaneSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    test_cases = [
        ("auto", HorizontalWindDirection.AUTO),
        ("left", HorizontalWindDirection.L),
        ("left_center", HorizontalWindDirection.LS),
        ("center", HorizontalWindDirection.C),
        ("right_center", HorizontalWindDirection.RS),
        ("right", HorizontalWindDirection.R),
        ("left_center_swing", HorizontalWindDirection.LC),
        ("center_right_swing", HorizontalWindDirection.CR),
        ("left_right_swing", HorizontalWindDirection.LR),
        ("all_positions", HorizontalWindDirection.LCR),
        ("swing", HorizontalWindDirection.LCR_S),
    ]

    for option, _ in test_cases:
        with patch.object(
            mock_coordinator, "async_request_refresh", new=AsyncMock()
        ) as mock_refresh, patch.object(
            hass, "async_add_executor_job", new=AsyncMock()
        ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
            await select.async_select_option(option)

            # Should call the lambda function wrapping the controller command
            assert mock_executor.call_count == 1
            mock_refresh.assert_called_once()
