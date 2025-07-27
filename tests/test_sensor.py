"""Tests for the sensor platform."""
import pytest
from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntry

from custom_components.mitsubishi.sensor import (
    MitsubishiRoomTemperatureSensor,
    MitsubishiOutdoorTemperatureSensor,
    MitsubishiDehumidifierLevelSensor,
    MitsubishiErrorSensor,
    MitsubishiUnitInfoSensor,
    async_setup_entry,
)
from custom_components.mitsubishi.const import DOMAIN

@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_coordinator, mock_config_entry):
    """Test the setup of Mitsubishi sensors."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 5
    assert isinstance(entities[0], MitsubishiRoomTemperatureSensor)
    assert isinstance(entities[1], MitsubishiOutdoorTemperatureSensor)
    assert isinstance(entities[2], MitsubishiErrorSensor)
    assert isinstance(entities[3], MitsubishiDehumidifierLevelSensor)
    assert isinstance(entities[4], MitsubishiUnitInfoSensor)


@pytest.mark.asyncio
async def test_room_temperature_sensor(hass, mock_coordinator, mock_config_entry):
    """Test room temperature sensor."""
    sensor = MitsubishiRoomTemperatureSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"room_temp": 22.5}
    assert sensor.native_value == 22.5
    assert sensor.extra_state_attributes == {"source": "Mitsubishi AC"}


@pytest.mark.asyncio
async def test_outdoor_temperature_sensor(hass, mock_coordinator, mock_config_entry):
    """Test outdoor temperature sensor."""
    sensor = MitsubishiOutdoorTemperatureSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"outside_temp": 18.0}
    assert sensor.native_value == 18.0
    assert sensor.extra_state_attributes == {"source": "Mitsubishi AC"}


@pytest.mark.asyncio
async def test_dehumidifier_level_sensor(hass, mock_coordinator, mock_config_entry):
    """Test dehumidifier level sensor."""
    sensor = MitsubishiDehumidifierLevelSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"dehumidifier_setting": 50}
    assert sensor.native_value == 50
    assert sensor.extra_state_attributes == {"source": "Mitsubishi AC"}


@pytest.mark.asyncio
async def test_error_sensor(hass, mock_coordinator, mock_config_entry):
    """Test error sensor."""
    sensor = MitsubishiErrorSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"error_code": "E001", "abnormal_state": True}
    assert sensor.native_value == "E001"
    assert sensor.extra_state_attributes == {"abnormal_state": True}


@pytest.mark.asyncio
async def test_error_sensor_default(hass, mock_coordinator, mock_config_entry):
    """Test error sensor with default values."""
    sensor = MitsubishiErrorSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {}
    assert sensor.native_value == "OK"
    assert sensor.extra_state_attributes == {"abnormal_state": False}


@pytest.mark.asyncio
async def test_unit_info_sensor(hass, mock_coordinator, mock_config_entry):
    """Test unit info sensor."""
    sensor = MitsubishiUnitInfoSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {
        "adaptor_info": {"model": "MAC-577IF-2E", "app_version": "1.0.0"},
        "unit_info": {"type": "Air Conditioner"}
    }
    assert sensor.native_value == "MAC-577IF-2E"
    assert sensor.extra_state_attributes == {
        "app_version": "1.0.0",
        "unit_type": "Air Conditioner"
    }


@pytest.mark.asyncio
async def test_unit_info_sensor_default(hass, mock_coordinator, mock_config_entry):
    """Test unit info sensor with default values."""
    sensor = MitsubishiUnitInfoSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {}
    assert sensor.native_value == "Unknown"
    assert sensor.extra_state_attributes == {"status": "Unit info not available"}


@pytest.mark.asyncio
async def test_room_temperature_sensor_none(hass, mock_coordinator, mock_config_entry):
    """Test room temperature sensor with None value."""
    sensor = MitsubishiRoomTemperatureSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {}
    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_outdoor_temperature_sensor_none(hass, mock_coordinator, mock_config_entry):
    """Test outdoor temperature sensor with None value."""
    sensor = MitsubishiOutdoorTemperatureSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {}
    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_dehumidifier_level_sensor_none(hass, mock_coordinator, mock_config_entry):
    """Test dehumidifier level sensor with None value."""
    sensor = MitsubishiDehumidifierLevelSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {}
    assert sensor.native_value is None
