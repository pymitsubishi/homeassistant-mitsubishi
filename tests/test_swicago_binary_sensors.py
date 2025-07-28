"""Tests for SwiCago-inspired binary sensors."""
from unittest.mock import MagicMock

import pytest

from custom_components.mitsubishi.binary_sensor import (
    MitsubishiISeeActiveBinarySensor,
    MitsubishiOperatingBinarySensor,
    MitsubishiWideVaneAdjustmentBinarySensor,
)


@pytest.mark.asyncio
async def test_i_see_active_binary_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test i-See active binary sensor initialization."""
    sensor = MitsubishiISeeActiveBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "i-See Sensor Active"
    assert sensor._attr_icon == "mdi:eye"
    assert sensor.unique_id.endswith("_i_see_active")


@pytest.mark.asyncio
async def test_i_see_active_binary_sensor_is_on_true(hass, mock_coordinator, mock_config_entry):
    """Test i-See active binary sensor when active."""
    mock_coordinator.data = {"i_see_sensor_active": True}

    sensor = MitsubishiISeeActiveBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_i_see_active_binary_sensor_is_on_false(hass, mock_coordinator, mock_config_entry):
    """Test i-See active binary sensor when inactive."""
    mock_coordinator.data = {"i_see_sensor_active": False}

    sensor = MitsubishiISeeActiveBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_i_see_active_binary_sensor_is_on_missing(hass, mock_coordinator, mock_config_entry):
    """Test i-See active binary sensor when data is missing."""
    mock_coordinator.data = {}

    sensor = MitsubishiISeeActiveBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_i_see_active_binary_sensor_availability(hass, mock_coordinator, mock_config_entry):
    """Test i-See active binary sensor availability."""
    # Test with controller state available
    mock_controller = MagicMock()
    mock_controller.state = MagicMock()
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiISeeActiveBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.available is True

    # Test with controller state None
    mock_controller.state = None
    assert sensor.available is False

    # Test with no controller
    mock_coordinator.controller = None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_i_see_active_binary_sensor_extra_state_attributes(hass, mock_coordinator, mock_config_entry):
    """Test i-See active binary sensor extra state attributes."""
    # Test with full controller state
    mock_controller = MagicMock()
    mock_general = MagicMock()
    mock_general.mode_raw_value = 0x01
    mock_general.drive_mode = MagicMock()
    mock_general.drive_mode.name = "COOL"
    mock_controller.state.general = mock_general
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiISeeActiveBinarySensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes["source"] == "SwiCago enhancement"
    assert attributes["mode_raw_value"] == "0x01"
    assert attributes["parsed_mode"] == "COOL"

    # Test with missing drive_mode
    mock_general.drive_mode = None
    attributes = sensor.extra_state_attributes
    assert "parsed_mode" not in attributes

    # Test with None mode_raw_value
    mock_general.mode_raw_value = None
    attributes = sensor.extra_state_attributes
    assert "mode_raw_value" not in attributes


@pytest.mark.asyncio
async def test_operating_binary_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test operating binary sensor initialization."""
    sensor = MitsubishiOperatingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Operating Status"
    assert sensor._attr_icon == "mdi:power"
    assert sensor.unique_id.endswith("_operating_status")


@pytest.mark.asyncio
async def test_operating_binary_sensor_is_on_true(hass, mock_coordinator, mock_config_entry):
    """Test operating binary sensor when operating."""
    mock_coordinator.data = {"energy_states": {"operating": True}}

    sensor = MitsubishiOperatingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_operating_binary_sensor_is_on_false(hass, mock_coordinator, mock_config_entry):
    """Test operating binary sensor when not operating."""
    mock_coordinator.data = {"energy_states": {"operating": False}}

    sensor = MitsubishiOperatingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_operating_binary_sensor_is_on_missing(hass, mock_coordinator, mock_config_entry):
    """Test operating binary sensor when data is missing."""
    mock_coordinator.data = {}

    sensor = MitsubishiOperatingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_operating_binary_sensor_availability(hass, mock_coordinator, mock_config_entry):
    """Test operating binary sensor availability."""
    # Test with controller state available
    mock_controller = MagicMock()
    mock_controller.state = MagicMock()
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiOperatingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.available is True

    # Test with controller state None
    mock_controller.state = None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_operating_binary_sensor_extra_state_attributes(hass, mock_coordinator, mock_config_entry):
    """Test operating binary sensor extra state attributes."""
    # Test with full energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.compressor_frequency = 45
    mock_energy.estimated_power_watts = 1200
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiOperatingBinarySensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes["source"] == "SwiCago enhancement"
    assert attributes["compressor_frequency"] == 45
    assert attributes["estimated_power_watts"] == 1200


@pytest.mark.asyncio
async def test_wide_vane_adjustment_binary_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test wide vane adjustment binary sensor initialization."""
    sensor = MitsubishiWideVaneAdjustmentBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Wide Vane Adjustment"
    assert sensor._attr_icon == "mdi:tune-vertical"
    assert sensor.unique_id.endswith("_wide_vane_adjustment")


@pytest.mark.asyncio
async def test_wide_vane_adjustment_binary_sensor_is_on_true(hass, mock_coordinator, mock_config_entry):
    """Test wide vane adjustment binary sensor when active."""
    mock_coordinator.data = {"wide_vane_adjustment": True}

    sensor = MitsubishiWideVaneAdjustmentBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_wide_vane_adjustment_binary_sensor_is_on_false(hass, mock_coordinator, mock_config_entry):
    """Test wide vane adjustment binary sensor when inactive."""
    mock_coordinator.data = {"wide_vane_adjustment": False}

    sensor = MitsubishiWideVaneAdjustmentBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_wide_vane_adjustment_binary_sensor_is_on_missing(hass, mock_coordinator, mock_config_entry):
    """Test wide vane adjustment binary sensor when data is missing."""
    mock_coordinator.data = {}

    sensor = MitsubishiWideVaneAdjustmentBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_wide_vane_adjustment_binary_sensor_availability(hass, mock_coordinator, mock_config_entry):
    """Test wide vane adjustment binary sensor availability."""
    # Test with controller state available
    mock_controller = MagicMock()
    mock_controller.state = MagicMock()
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiWideVaneAdjustmentBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.available is True

    # Test with controller state None
    mock_controller.state = None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_wide_vane_adjustment_binary_sensor_extra_state_attributes(hass, mock_coordinator, mock_config_entry):
    """Test wide vane adjustment binary sensor extra state attributes."""
    # Test with full general state
    mock_controller = MagicMock()
    mock_general = MagicMock()
    mock_general.horizontal_wind_direction = MagicMock()
    mock_general.horizontal_wind_direction.name = "LEFT"
    mock_controller.state.general = mock_general
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiWideVaneAdjustmentBinarySensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes["source"] == "SwiCago enhancement"
    assert attributes["horizontal_wind_direction"] == "LEFT"

    # Test with missing horizontal_wind_direction
    mock_general.horizontal_wind_direction = None
    attributes = sensor.extra_state_attributes
    assert "horizontal_wind_direction" not in attributes
