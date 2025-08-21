import pytest

from custom_components.mitsubishi.sensor import (
    MitsubishiSensor,
)


@pytest.mark.asyncio
async def test_sensor_getter(mock_coordinator, mock_config_entry):
    mock_coordinator.data.general.fine_temperature = 21.5
    sensor = MitsubishiSensor(
        mock_coordinator, mock_config_entry,
        "test name", "test key",
        lambda d: d.general.temperature,
    )

    assert sensor.native_value == 21.5
