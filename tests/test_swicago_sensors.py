"""Tests for SwiCago-inspired sensors and energy monitoring sensors."""
from unittest.mock import MagicMock

import pytest

from custom_components.mitsubishi.sensor import (
    MitsubishiCompressorFrequencySensor,
    MitsubishiEnergyAutoSensor,
    MitsubishiEnergyCoolingSensor,
    MitsubishiEnergyDrySensor,
    MitsubishiEnergyFanSensor,
    MitsubishiEnergyHeatingSensor,
    MitsubishiEnergyTotalSensor,
    MitsubishiEstimatedPowerSensor,
    MitsubishiModeRawValueSensor,
    MitsubishiTemperatureModeSensor,
)


@pytest.mark.asyncio
async def test_compressor_frequency_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test compressor frequency sensor initialization."""
    sensor = MitsubishiCompressorFrequencySensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Compressor Frequency"
    assert sensor._attr_icon == "mdi:fan"
    assert sensor._attr_native_unit_of_measurement == "Hz"
    assert sensor.unique_id.endswith("_compressor_frequency")


@pytest.mark.asyncio
async def test_compressor_frequency_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test compressor frequency sensor native value."""
    mock_coordinator.data = {"energy_states": {"compressor_frequency": 45}}

    sensor = MitsubishiCompressorFrequencySensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == 45
    assert sensor.available is True


@pytest.mark.asyncio
async def test_compressor_frequency_sensor_native_value_none(
    hass, mock_coordinator, mock_config_entry
):
    """Test compressor frequency sensor with None value."""
    mock_coordinator.data = {}

    sensor = MitsubishiCompressorFrequencySensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value is None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_compressor_frequency_sensor_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test compressor frequency sensor extra state attributes."""
    # Test with full energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.operating = True
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiCompressorFrequencySensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes["source"] == "SwiCago enhancement"
    assert attributes["operating"] is True


@pytest.mark.asyncio
async def test_estimated_power_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test estimated power sensor initialization."""
    sensor = MitsubishiEstimatedPowerSensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Estimated Power"
    assert sensor._attr_native_unit_of_measurement == "W"
    assert sensor.unique_id.endswith("_estimated_power")


@pytest.mark.asyncio
async def test_estimated_power_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test estimated power sensor native value."""
    mock_coordinator.data = {"energy_states": {"estimated_power_watts": 1200.5}}

    sensor = MitsubishiEstimatedPowerSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == 1200.5
    assert sensor.available is True


@pytest.mark.asyncio
async def test_estimated_power_sensor_native_value_none(hass, mock_coordinator, mock_config_entry):
    """Test estimated power sensor with None value."""
    mock_coordinator.data = {}

    sensor = MitsubishiEstimatedPowerSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value is None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_estimated_power_sensor_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test estimated power sensor extra state attributes."""
    # Test with full energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.compressor_frequency = 45
    mock_energy.operating = True
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEstimatedPowerSensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes["source"] == "SwiCago enhancement"
    assert attributes["estimation_method"] == "Compressor frequency + mode + fan speed"
    assert attributes["accuracy"] == "Rough estimate - varies with conditions"
    assert attributes["compressor_frequency"] == 45
    assert attributes["operating_status"] is True


@pytest.mark.asyncio
async def test_mode_raw_value_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test mode raw value sensor initialization."""
    sensor = MitsubishiModeRawValueSensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Mode Raw Value"
    assert sensor._attr_icon == "mdi:code-brackets"
    assert sensor.unique_id.endswith("_mode_raw_value")


@pytest.mark.asyncio
async def test_mode_raw_value_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test mode raw value sensor native value."""
    mock_coordinator.data = {"mode_raw_value": 0x01}

    sensor = MitsubishiModeRawValueSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == "0x01"
    assert sensor.available is True


@pytest.mark.asyncio
async def test_mode_raw_value_sensor_native_value_none(hass, mock_coordinator, mock_config_entry):
    """Test mode raw value sensor with None value."""
    mock_coordinator.data = {}

    sensor = MitsubishiModeRawValueSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value is None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_mode_raw_value_sensor_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test mode raw value sensor extra state attributes."""
    # Test with full general state
    mock_controller = MagicMock()
    mock_general = MagicMock()
    mock_general.i_see_sensor = True
    mock_general.drive_mode = MagicMock()
    mock_general.drive_mode.name = "COOL"
    mock_general.wide_vane_adjustment = False
    mock_controller.state.general = mock_general
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiModeRawValueSensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes["source"] == "SwiCago enhancement"
    assert attributes["i_see_sensor_active"] is True
    assert attributes["parsed_mode"] == "COOL"
    assert attributes["wide_vane_adjustment"] is False

    # Test with missing drive_mode
    mock_general.drive_mode = None
    attributes = sensor.extra_state_attributes
    assert "parsed_mode" not in attributes


@pytest.mark.asyncio
async def test_temperature_mode_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test temperature mode sensor initialization."""
    sensor = MitsubishiTemperatureModeSensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Temperature Mode"
    assert sensor._attr_icon == "mdi:thermometer-lines"
    assert sensor.unique_id.endswith("_temperature_mode")


@pytest.mark.asyncio
async def test_temperature_mode_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test temperature mode sensor native value."""
    mock_coordinator.data = {"temperature_mode": "direct"}

    sensor = MitsubishiTemperatureModeSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == "Direct"
    assert sensor.available is True


@pytest.mark.asyncio
async def test_temperature_mode_sensor_native_value_none(hass, mock_coordinator, mock_config_entry):
    """Test temperature mode sensor with None value."""
    mock_coordinator.data = {}

    sensor = MitsubishiTemperatureModeSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value is None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_temperature_mode_sensor_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test temperature mode sensor extra state attributes."""
    # Test with full general state
    mock_controller = MagicMock()
    mock_general = MagicMock()
    mock_general.temperature = 225  # 22.5°C in tenths
    mock_controller.state.general = mock_general
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiTemperatureModeSensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes["source"] == "SwiCago enhancement"
    assert (
        attributes["description"]
        == "Direct mode uses precise temperature values, Segment mode uses predefined steps"
    )
    assert attributes["current_temperature_celsius"] == 22.5

    # Test with None temperature
    mock_general.temperature = None
    attributes = sensor.extra_state_attributes
    assert "current_temperature_celsius" not in attributes


# Energy monitoring sensor tests
@pytest.mark.asyncio
async def test_energy_total_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test energy total sensor initialization."""
    sensor = MitsubishiEnergyTotalSensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Total Energy"
    assert sensor._attr_icon == "mdi:lightning-bolt"
    assert sensor._attr_native_unit_of_measurement == "kWh"
    assert sensor.unique_id.endswith("_energy_total")


@pytest.mark.asyncio
async def test_energy_total_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test energy total sensor native value."""
    # Mock the controller with energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.energy_total_kWh = 150.5  # Already in kWh
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEnergyTotalSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == 0.1505  # Converted from Wh to kWh (÷1000)
    assert sensor.available is True


@pytest.mark.asyncio
async def test_energy_total_sensor_native_value_none(hass, mock_coordinator, mock_config_entry):
    """Test energy total sensor with None value."""
    # Clear any existing controller mock
    mock_coordinator.controller = None

    sensor = MitsubishiEnergyTotalSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value is None
    assert sensor.available is False


@pytest.mark.asyncio
async def test_energy_total_sensor_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test energy total sensor extra state attributes."""
    # Test with full energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.operating = True
    mock_energy.compressor_frequency = 45
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEnergyTotalSensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes["source"] == "Energy monitoring"
    assert attributes["energy_type"] == "total"
    assert attributes["unit_conversion"] == "Wh to kWh (÷1000)"
    assert attributes["operating_status"] is True
    assert attributes["compressor_frequency"] == 45


@pytest.mark.asyncio
async def test_energy_cooling_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test energy cooling sensor initialization."""
    sensor = MitsubishiEnergyCoolingSensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Cooling Energy"
    assert sensor._attr_icon == "mdi:snowflake"
    assert sensor.unique_id.endswith("_energy_cooling")


@pytest.mark.asyncio
async def test_energy_cooling_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test energy cooling sensor native value."""
    # Mock the controller with energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.energy_total_cooling_kWh = 75.25
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEnergyCoolingSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == 0.07525  # Converted from Wh to kWh (÷1000)
    assert sensor.available is True


@pytest.mark.asyncio
async def test_energy_heating_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test energy heating sensor initialization."""
    sensor = MitsubishiEnergyHeatingSensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Heating Energy"
    assert sensor._attr_icon == "mdi:fire"
    assert sensor.unique_id.endswith("_energy_heating")


@pytest.mark.asyncio
async def test_energy_heating_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test energy heating sensor native value."""
    # Mock the controller with energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.energy_total_heating_kWh = 100.0
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEnergyHeatingSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == 0.1  # Converted from Wh to kWh (÷1000)
    assert sensor.available is True


@pytest.mark.asyncio
async def test_energy_auto_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test energy auto sensor initialization."""
    sensor = MitsubishiEnergyAutoSensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Auto Mode Energy"
    assert sensor._attr_icon == "mdi:thermostat-auto"
    assert sensor.unique_id.endswith("_energy_auto")


@pytest.mark.asyncio
async def test_energy_auto_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test energy auto sensor native value."""
    # Mock the controller with energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.energy_total_auto_kWh = 50.0
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEnergyAutoSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == 0.05  # Converted from Wh to kWh (÷1000)
    assert sensor.available is True


@pytest.mark.asyncio
async def test_energy_dry_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test energy dry sensor initialization."""
    sensor = MitsubishiEnergyDrySensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Dry Mode Energy"
    assert sensor._attr_icon == "mdi:water-percent"
    assert sensor.unique_id.endswith("_energy_dry")


@pytest.mark.asyncio
async def test_energy_dry_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test energy dry sensor native value."""
    # Mock the controller with energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.energy_total_dry_kWh = 25.0
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEnergyDrySensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == 0.025  # Converted from Wh to kWh (÷1000)
    assert sensor.available is True


@pytest.mark.asyncio
async def test_energy_fan_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test energy fan sensor initialization."""
    sensor = MitsubishiEnergyFanSensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Fan Mode Energy"
    assert sensor._attr_icon == "mdi:fan"
    assert sensor.unique_id.endswith("_energy_fan")


@pytest.mark.asyncio
async def test_energy_fan_sensor_native_value(hass, mock_coordinator, mock_config_entry):
    """Test energy fan sensor native value."""
    # Mock the controller with energy state
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    mock_energy.energy_total_fan_kWh = 10.0
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEnergyFanSensor(mock_coordinator, mock_config_entry)

    assert sensor.native_value == 0.01  # Converted from Wh to kWh (÷1000)
    assert sensor.available is True


@pytest.mark.asyncio
async def test_energy_sensor_missing_attribute(hass, mock_coordinator, mock_config_entry):
    """Test energy sensor when the specific attribute is missing."""
    # Mock the controller with energy state but without the specific attribute
    mock_controller = MagicMock()
    mock_energy = MagicMock()
    # Make hasattr return False for the specific attribute
    del mock_energy.energy_total_kWh
    mock_controller.state.energy = mock_energy
    mock_coordinator.controller = mock_controller

    sensor = MitsubishiEnergyTotalSensor(mock_coordinator, mock_config_entry)

    # Should return None when the attribute doesn't exist
    assert sensor.native_value is None
    assert sensor.available is False
