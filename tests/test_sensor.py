"""Tests for the sensor platform."""
from unittest.mock import MagicMock, patch

import pytest

from custom_components.mitsubishi.const import DOMAIN
from custom_components.mitsubishi.sensor import (
    MitsubishiDehumidifierLevelSensor,
    MitsubishiErrorSensor,
    MitsubishiFirmwareVersionSensor,
    MitsubishiOutdoorTemperatureSensor,
    MitsubishiRoomTemperatureSensor,
    MitsubishiUnitInfoSensor,
    MitsubishiUnitTypeSensor,
    MitsubishiWifiInfoSensor,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_coordinator, mock_config_entry):
    """Test the setup of Mitsubishi sensors."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 8
    assert isinstance(entities[0], MitsubishiRoomTemperatureSensor)
    assert isinstance(entities[1], MitsubishiOutdoorTemperatureSensor)
    assert isinstance(entities[2], MitsubishiErrorSensor)
    assert isinstance(entities[3], MitsubishiDehumidifierLevelSensor)
    assert isinstance(entities[4], MitsubishiUnitInfoSensor)
    assert isinstance(entities[5], MitsubishiFirmwareVersionSensor)
    assert isinstance(entities[6], MitsubishiUnitTypeSensor)
    assert isinstance(entities[7], MitsubishiWifiInfoSensor)


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


@pytest.mark.asyncio
async def test_firmware_version_sensor(hass, mock_coordinator, mock_config_entry):
    """Test firmware version sensor."""
    sensor = MitsubishiFirmwareVersionSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {
        "adaptor_info": {
            "app_version": "1.2.3",
            "release_version": "4.5.6",
            "flash_version": "7.8.9",
            "boot_version": "1.0.1",
            "platform_version": "2.0.2",
        },
        "unit_info": {
            "it_protocol_version": "3.0.3"
        }
    }
    assert sensor.native_value == "1.2.3"
    assert sensor.extra_state_attributes == {
        "release_version": "4.5.6",
        "flash_version": "7.8.9",
        "boot_version": "1.0.1",
        "platform_version": "2.0.2",
        "protocol_version": "3.0.3",
    }


@pytest.mark.asyncio
async def test_firmware_version_sensor_default(hass, mock_coordinator, mock_config_entry):
    """Test firmware version sensor with default values."""
    sensor = MitsubishiFirmwareVersionSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {}
    assert sensor.native_value == "Unknown"
    assert sensor.extra_state_attributes == {"status": "Unit info not available"}


@pytest.mark.asyncio
async def test_unit_type_sensor(hass, mock_coordinator, mock_config_entry):
    """Test unit type sensor."""
    sensor = MitsubishiUnitTypeSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {
        "adaptor_info": {
            "model": "MAC-577IF-2E",
            "device_id": "DEV123",
            "manufacturing_date": "2023-01-01",
        },
        "unit_info": {
            "type": "Air Conditioner",
            "it_protocol_version": "3.0.3",
            "error_code": "0000",
        }
    }
    assert sensor.native_value == "Air Conditioner"
    assert sensor.extra_state_attributes == {
        "model": "MAC-577IF-2E",
        "device_id": "DEV123",
        "manufacturing_date": "2023-01-01",
        "protocol_version": "3.0.3",
        "unit_error_code": "0000",
    }


@pytest.mark.asyncio
async def test_unit_type_sensor_default(hass, mock_coordinator, mock_config_entry):
    """Test unit type sensor with default values."""
    sensor = MitsubishiUnitTypeSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {}
    assert sensor.native_value == "Unknown"
    assert sensor.extra_state_attributes == {"status": "Unit info not available"}


@pytest.mark.asyncio
async def test_wifi_info_sensor(hass, mock_coordinator, mock_config_entry):
    """Test WiFi info sensor."""
    sensor = MitsubishiWifiInfoSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {
        "adaptor_info": {
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "wifi_channel": 6,
            "rssi_dbm": -45,
            "it_comm_status": "OK",
            "server_operation": "active",
            "server_comm_status": "connected",
        }
    }
    assert sensor.native_value == "-45 dBm"
    assert sensor.extra_state_attributes == {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "wifi_channel": 6,
        "rssi_dbm": -45,
        "it_comm_status": "OK",
        "server_operation": "active",
        "server_comm_status": "connected",
    }


@pytest.mark.asyncio
async def test_wifi_info_sensor_default(hass, mock_coordinator, mock_config_entry):
    """Test WiFi info sensor with default values."""
    sensor = MitsubishiWifiInfoSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {}
    assert sensor.native_value == "Unknown"
    assert sensor.extra_state_attributes == {"status": "Unit info not available"}


@pytest.mark.asyncio
async def test_wifi_info_sensor_no_rssi(hass, mock_coordinator, mock_config_entry):
    """Test WiFi info sensor without RSSI data."""
    sensor = MitsubishiWifiInfoSensor(mock_coordinator, mock_config_entry)
    mock_coordinator.unit_info = {
        "adaptor_info": {
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "wifi_channel": 6,
        }
    }
    assert sensor.native_value == "Unknown"
    assert sensor.extra_state_attributes == {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "wifi_channel": 6,
    }


@pytest.mark.asyncio
async def test_base_diagnostic_sensor_helper_methods(hass, mock_coordinator, mock_config_entry):
    """Test the helper methods in BaseMitsubishiDiagnosticSensor."""
    sensor = MitsubishiFirmwareVersionSensor(mock_coordinator, mock_config_entry)

    # Test _filter_none_values
    test_dict = {"key1": "value1", "key2": None, "key3": "value3"}
    filtered = sensor._filter_none_values(test_dict)
    assert filtered == {"key1": "value1", "key3": "value3"}

    # Test _get_unavailable_status
    status = sensor._get_unavailable_status()
    assert status == {"status": "Unit info not available"}

    # Test _get_unit_info_data with no unit_info
    mock_coordinator.unit_info = None
    adaptor_info, unit_info = sensor._get_unit_info_data()
    assert adaptor_info == {}
    assert unit_info == {}


@pytest.mark.asyncio
async def test_async_setup_entry_sensor_creation_none(hass, mock_coordinator, mock_config_entry):
    """Test async_setup_entry when sensor creation returns None."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()

    # Mock one sensor class to return None
    with patch('custom_components.mitsubishi.sensor.MitsubishiRoomTemperatureSensor', return_value=None):
        await async_setup_entry(hass, mock_config_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    # Should have 7 entities instead of 8 since one returned None
    assert len(entities) == 7


@pytest.mark.asyncio
async def test_async_setup_entry_sensor_creation_exception(hass, mock_coordinator, mock_config_entry):
    """Test async_setup_entry when sensor creation raises an exception."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()

    # Mock one sensor class to raise an exception
    with patch('custom_components.mitsubishi.sensor.MitsubishiOutdoorTemperatureSensor', side_effect=Exception("Test exception")):
        await async_setup_entry(hass, mock_config_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    # Should have 7 entities instead of 8 since one failed to create
    assert len(entities) == 7
