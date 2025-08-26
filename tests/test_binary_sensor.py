import pytest

from custom_components.mitsubishi.binary_sensor import (
    MitsubishiBinarySensor,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "v",
    [True, False],
)
async def test_sensor_getter(mock_coordinator, mock_config_entry, v):
    mock_coordinator.data.energy.operating = v
    sensor = MitsubishiBinarySensor(
        mock_coordinator,
        mock_config_entry,
        "test name",
        "test key",
        lambda d: d.energy.operating,
    )

    assert sensor.is_on is v
