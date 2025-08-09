"""Tests for the binary sensor platform."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.mitsubishi.binary_sensor import (
    MitsubishiErrorBinarySensor,
    MitsubishiPowerSavingBinarySensor,
    async_setup_entry,
)
from custom_components.mitsubishi.const import DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_coordinator, mock_config_entry):
    """Test the async_setup_entry function."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}

    async_add_entities = MagicMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]

    assert len(entities) == 5
    assert isinstance(entities[0], MitsubishiPowerSavingBinarySensor)
    assert isinstance(entities[1], MitsubishiErrorBinarySensor)
    # Additional SwiCago-inspired sensors are also created


@pytest.mark.asyncio
async def test_power_saving_binary_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test power saving binary sensor initialization."""
    sensor = MitsubishiPowerSavingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Power Saving Mode"
    assert sensor._attr_icon == "mdi:leaf"
    assert sensor.unique_id.endswith("_power_saving_mode")


@pytest.mark.asyncio
async def test_power_saving_binary_sensor_is_on_true(hass, mock_coordinator, mock_config_entry):
    """Test power saving binary sensor when power saving mode is enabled."""
    mock_coordinator.data = {"power_saving_mode": True}

    sensor = MitsubishiPowerSavingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_power_saving_binary_sensor_is_on_false(hass, mock_coordinator, mock_config_entry):
    """Test power saving binary sensor when power saving mode is disabled."""
    mock_coordinator.data = {"power_saving_mode": False}

    sensor = MitsubishiPowerSavingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_power_saving_binary_sensor_is_on_missing(hass, mock_coordinator, mock_config_entry):
    """Test power saving binary sensor when power saving mode data is missing."""
    mock_coordinator.data = {}

    sensor = MitsubishiPowerSavingBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_power_saving_binary_sensor_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving binary sensor extra state attributes."""
    sensor = MitsubishiPowerSavingBinarySensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes == {"source": "Mitsubishi AC"}


@pytest.mark.asyncio
async def test_error_binary_sensor_init(hass, mock_coordinator, mock_config_entry):
    """Test error binary sensor initialization."""
    sensor = MitsubishiErrorBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor._attr_name == "Error State"
    assert sensor._attr_device_class == BinarySensorDeviceClass.PROBLEM
    assert sensor._attr_icon == "mdi:alert-circle"
    assert sensor.unique_id.endswith("_error_state")


@pytest.mark.asyncio
async def test_error_binary_sensor_is_on_abnormal_state(hass, mock_coordinator, mock_config_entry):
    """Test error binary sensor when abnormal state is true."""
    mock_coordinator.data = {"abnormal_state": True, "error_code": "8000"}

    sensor = MitsubishiErrorBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_error_binary_sensor_is_on_error_code(hass, mock_coordinator, mock_config_entry):
    """Test error binary sensor when error code indicates an error."""
    mock_coordinator.data = {"abnormal_state": False, "error_code": "E001"}

    sensor = MitsubishiErrorBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_error_binary_sensor_is_on_ok_error_code(hass, mock_coordinator, mock_config_entry):
    """Test error binary sensor when error code is OK."""
    mock_coordinator.data = {"abnormal_state": False, "error_code": "OK"}

    sensor = MitsubishiErrorBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_error_binary_sensor_is_on_no_error(hass, mock_coordinator, mock_config_entry):
    """Test error binary sensor when there is no error."""
    mock_coordinator.data = {"abnormal_state": False, "error_code": "8000"}

    sensor = MitsubishiErrorBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_error_binary_sensor_is_on_missing_data(hass, mock_coordinator, mock_config_entry):
    """Test error binary sensor when error data is missing."""
    mock_coordinator.data = {}

    sensor = MitsubishiErrorBinarySensor(mock_coordinator, mock_config_entry)

    assert sensor.is_on is False


@pytest.mark.asyncio
async def test_error_binary_sensor_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test error binary sensor extra state attributes."""
    mock_coordinator.data = {"error_code": "E001", "abnormal_state": True}

    sensor = MitsubishiErrorBinarySensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes == {"error_code": "E001", "abnormal_state": True}


@pytest.mark.asyncio
async def test_error_binary_sensor_extra_state_attributes_defaults(
    hass, mock_coordinator, mock_config_entry
):
    """Test error binary sensor extra state attributes with default values."""
    mock_coordinator.data = {}

    sensor = MitsubishiErrorBinarySensor(mock_coordinator, mock_config_entry)

    attributes = sensor.extra_state_attributes
    assert attributes == {"error_code": "8000", "abnormal_state": False}
