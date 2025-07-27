"""Tests for the number platform."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from homeassistant.components.number import NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE

from custom_components.mitsubishi.number import (
    MitsubishiDehumidifierNumber,
    async_setup_entry,
)
from custom_components.mitsubishi.const import DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_coordinator, mock_config_entry):
    """Test the setup of Mitsubishi number entities."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], MitsubishiDehumidifierNumber)


@pytest.mark.asyncio
async def test_dehumidifier_number_init(hass, mock_coordinator, mock_config_entry):
    """Test dehumidifier number entity initialization."""
    number = MitsubishiDehumidifierNumber(mock_coordinator, mock_config_entry)
    
    assert number._attr_name == "Dehumidifier Level"
    assert number._attr_icon == "mdi:water-percent"
    assert number._attr_native_min_value == 0
    assert number._attr_native_max_value == 100
    assert number._attr_native_step == 5
    assert number._attr_native_unit_of_measurement == PERCENTAGE
    assert number._attr_mode == NumberMode.SLIDER
    assert number.unique_id.endswith("_dehumidifier_control")


@pytest.mark.asyncio
async def test_dehumidifier_number_native_value(hass, mock_coordinator, mock_config_entry):
    """Test dehumidifier number native value property."""
    number = MitsubishiDehumidifierNumber(mock_coordinator, mock_config_entry)
    
    # Test with dehumidifier setting data
    mock_coordinator.data = {"dehumidifier_setting": 75}
    assert number.native_value == 75.0
    
    # Test without dehumidifier setting data
    mock_coordinator.data = {}
    assert number.native_value is None


@pytest.mark.asyncio
async def test_dehumidifier_number_native_value_string(hass, mock_coordinator, mock_config_entry):
    """Test dehumidifier number native value with string input."""
    number = MitsubishiDehumidifierNumber(mock_coordinator, mock_config_entry)
    
    # Test with string value that converts to float
    mock_coordinator.data = {"dehumidifier_setting": "50"}
    assert number.native_value == 50.0


@pytest.mark.asyncio
async def test_async_set_native_value_success(hass, mock_coordinator, mock_config_entry):
    """Test setting dehumidifier level successfully."""
    number = MitsubishiDehumidifierNumber(mock_coordinator, mock_config_entry)
    number.hass = hass  # Set hass attribute

    # Mock successful controller call
    with patch.object(mock_coordinator, 'async_request_refresh', new=AsyncMock()) as mock_refresh, \
         patch.object(hass, 'async_add_executor_job', new=AsyncMock()) as mock_executor:
        
        await number.async_set_native_value(65.0)

        mock_executor.assert_called_once_with(
            mock_coordinator.controller.set_dehumidifier, 65, False
        )
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_set_native_value_failure(hass, mock_coordinator, mock_config_entry):
    """Test setting dehumidifier level when controller returns failure."""
    number = MitsubishiDehumidifierNumber(mock_coordinator, mock_config_entry)
    number.hass = hass  # Set hass attribute
    
    # Mock failed controller call and capture the error logging
    with patch.object(hass, 'async_add_executor_job', new=AsyncMock(return_value=False)) as mock_executor, \
         patch('custom_components.mitsubishi.number._LOGGER.error') as mock_logger_error:
        await number.async_set_native_value(40.0)
        
        mock_executor.assert_called_with(
            mock_coordinator.controller.set_dehumidifier, 40, False
        )
        # Should not call refresh on failure
        mock_coordinator.async_request_refresh.assert_not_called()
        
        # Verify the error was logged (this covers line 73)
        mock_logger_error.assert_called_once_with("Failed to set dehumidifier level to %s", 40.0)


@pytest.mark.asyncio
async def test_async_set_native_value_exception(hass, mock_coordinator, mock_config_entry):
    """Test setting dehumidifier level when an exception occurs."""
    number = MitsubishiDehumidifierNumber(mock_coordinator, mock_config_entry)
    number.hass = hass  # Set hass attribute
    
    # Mock exception during controller call
    with patch.object(hass, 'async_add_executor_job', side_effect=Exception("Network error")) as mock_executor:
        # Should not raise exception, just log it
        await number.async_set_native_value(30.0)
        
        mock_executor.assert_called_with(
            mock_coordinator.controller.set_dehumidifier, 30, False
        )
        mock_coordinator.async_request_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_dehumidifier_number_extra_state_attributes(hass, mock_coordinator, mock_config_entry):
    """Test dehumidifier number extra state attributes."""
    number = MitsubishiDehumidifierNumber(mock_coordinator, mock_config_entry)
    
    attributes = number.extra_state_attributes
    assert attributes == {"source": "Mitsubishi AC"}


@pytest.mark.asyncio
async def test_async_set_native_value_float_conversion(hass, mock_coordinator, mock_config_entry):
    """Test that float values are properly converted to integers for the controller."""
    number = MitsubishiDehumidifierNumber(mock_coordinator, mock_config_entry)
    number.hass = hass  # Set hass attribute
    
    # Test that 85.7 gets converted to 85 (int)
    with patch.object(mock_coordinator, 'async_request_refresh', new=AsyncMock()) as mock_refresh, \
         patch.object(hass, 'async_add_executor_job', new=AsyncMock()) as mock_executor:
        
        await number.async_set_native_value(85.7)
        
        mock_executor.assert_called_once_with(
            mock_coordinator.controller.set_dehumidifier, 85, False  # Note: int(85.7) = 85
        )
        mock_refresh.assert_called_once()
