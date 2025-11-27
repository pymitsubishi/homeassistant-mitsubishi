"""Tests for the climate platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pymitsubishi
import pytest
import requests.exceptions
from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.mitsubishi.climate import (
    MitsubishiClimate,
    async_setup_entry,
)
from custom_components.mitsubishi.const import DOMAIN
from tests import TEST_SYSTEM_DATA


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_coordinator, mock_config_entry):
    """Test the setup of Mitsubishi climate entity."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], MitsubishiClimate)


@pytest.mark.asyncio
async def test_climate_init(hass, mock_coordinator, mock_config_entry):
    """Test climate entity initialization."""
    mock_coordinator.data = TEST_SYSTEM_DATA
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)

    assert climate._config_entry == mock_config_entry
    assert climate.unique_id == "00:11:22:33:44:55_climate"


@pytest.mark.asyncio
async def test_current_temperature(hass, mock_coordinator, mock_config_entry):
    """Test current temperature property."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)

    # Test with temperature data
    assert climate.current_temperature == 24.5

    # Test without temperature data
    mock_coordinator.data = {}
    assert climate.current_temperature is None


@pytest.mark.asyncio
async def test_target_temperature(hass, mock_coordinator, mock_config_entry):
    """Test target temperature property."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.fine_temperature = 22.0

    # Test with target temperature data
    assert climate.target_temperature == 22.0

    # Test without target temperature data
    mock_coordinator.data = None
    assert climate.target_temperature is None


@pytest.mark.asyncio
async def test_hvac_mode_off(hass, mock_coordinator, mock_config_entry):
    """Test HVAC mode when power is off."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.OFF
    assert climate.hvac_mode == HVACMode.OFF


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mitsubishi_mode,expected_ha_mode",
    [
        (pymitsubishi.DriveMode.HEATER, HVACMode.HEAT),
        (pymitsubishi.DriveMode.COOLER, HVACMode.COOL),
        (pymitsubishi.DriveMode.AUTO, HVACMode.AUTO),
    ],
)
async def test_hvac_mode(
    hass, mock_coordinator, mock_config_entry, mitsubishi_mode, expected_ha_mode
):
    """Test HVAC mode when set to heat."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.ON
    mock_coordinator.data.general.drive_mode = mitsubishi_mode
    assert climate.hvac_mode == expected_ha_mode


@pytest.mark.asyncio
async def test_hvac_action_off(hass, mock_coordinator, mock_config_entry):
    """Test HVAC action when power is off."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.OFF
    assert climate.hvac_action == HVACAction.OFF


@pytest.mark.asyncio
async def test_hvac_action_idle(hass, mock_coordinator, mock_config_entry):
    """Test HVAC action when power is off."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.ON
    mock_coordinator.data.energy.operating = False
    mock_coordinator.data.general.drive_mode = pymitsubishi.DriveMode.COOLER
    assert climate.hvac_action == HVACAction.IDLE


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mitsubishi_mode,,expected_ha_action",
    [
        (pymitsubishi.DriveMode.HEATER, HVACAction.HEATING),
        (pymitsubishi.DriveMode.COOLER, HVACAction.COOLING),
        (pymitsubishi.DriveMode.DEHUM, HVACAction.DRYING),
    ],
)
async def test_hvac_action_heating(
    hass, mock_coordinator, mock_config_entry, mitsubishi_mode, expected_ha_action
):
    """Test HVAC action when heating."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.ON
    mock_coordinator.data.energy.operating = True
    mock_coordinator.data.general.drive_mode = mitsubishi_mode
    assert climate.hvac_action == expected_ha_action


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mitsubishi_wind,expected_ha_fan",
    [
        (pymitsubishi.WindSpeed.AUTO, FAN_AUTO),
        (pymitsubishi.WindSpeed.S1, FAN_LOW),
        (pymitsubishi.WindSpeed.S3, FAN_MEDIUM),
        (pymitsubishi.WindSpeed.S4, FAN_HIGH),
    ],
)
async def test_fan_mode(
    hass, mock_coordinator, mock_config_entry, mitsubishi_wind, expected_ha_fan
):
    """Test fan mode when set to low."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.wind_speed = mitsubishi_wind
    assert climate.fan_mode == expected_ha_fan


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mitsubishi_vvane, expected_ha_swing",
    [
        (pymitsubishi.VerticalWindDirection.AUTO, "auto"),
        (pymitsubishi.VerticalWindDirection.V1, "1"),
        (pymitsubishi.VerticalWindDirection.V5, "5"),
        (pymitsubishi.VerticalWindDirection.SWING, "swing"),
    ],
)
async def test_swing_mode(
    hass, mock_coordinator, mock_config_entry, mitsubishi_vvane, expected_ha_swing
):
    """Test swing mode (currently always returns OFF)."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.vertical_wind_direction = mitsubishi_vvane
    assert climate.swing_mode == expected_ha_swing


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mitsubishi_hvane, expected_ha_hswing",
    [
        (pymitsubishi.HorizontalWindDirection.AUTO, "auto"),
        (pymitsubishi.HorizontalWindDirection.FAR_LEFT, "far left"),
        (pymitsubishi.HorizontalWindDirection.LEFT, "left"),
        (pymitsubishi.HorizontalWindDirection.SWING, "swing"),
    ],
)
async def test_horizontal_swing_mode(
    hass, mock_coordinator, mock_config_entry, mitsubishi_hvane, expected_ha_hswing
):
    """Test swing mode (currently always returns OFF)."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.horizontal_wind_direction = mitsubishi_hvane
    assert climate.swing_horizontal_mode == expected_ha_hswing


@pytest.mark.asyncio
async def test_extra_state_attributes(hass, mock_coordinator, mock_config_entry):
    """Test extra state attributes."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    attributes = climate.extra_state_attributes
    assert attributes["outdoor_temperature"] == 21.0
    assert attributes["power_saving_mode"] is False
    assert attributes["dehumidifier_setting"] == 0
    assert attributes["error_code"] == 0x8000
    assert attributes["abnormal_state"] is False


@pytest.mark.asyncio
async def test_async_set_temperature(
    hass, mock_coordinator, mock_config_entry, mock_async_methods, create_entity_with_setup
):
    """Test setting temperature directly on entity."""
    climate = create_entity_with_setup(
        MitsubishiClimate, mock_coordinator, mock_config_entry, hass=hass
    )

    # Mock controller data to ensure target_temp matches expected (to avoid validation failure)
    mock_coordinator.data = {"target_temp": 25.0}

    # Mock the controller method and coordinator refresh
    with (
        patch.object(mock_coordinator.controller, "set_temperature"),
        mock_async_methods(hass, mock_coordinator) as (mock_executor, mock_refresh),
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 25.0})

        # Verify the executor was called once (centralized approach)
        assert mock_executor.call_count == 1
        # async_request_refresh should be called once for successful temperature commands
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_set_temperature_none(hass, mock_coordinator, mock_config_entry):
    """Test setting temperature with None value."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)

    with patch.object(hass, "async_add_executor_job") as mock_executor:
        await climate.async_set_temperature()

        mock_executor.assert_not_called()


@pytest.mark.asyncio
async def test_async_set_hvac_mode_off(
    hass, mock_coordinator, mock_config_entry, mock_async_methods, create_entity_with_setup
):
    """Test setting HVAC mode to off."""
    climate = create_entity_with_setup(
        MitsubishiClimate, mock_coordinator, mock_config_entry, hass=hass
    )

    with (
        mock_async_methods(hass, mock_coordinator) as (mock_executor, mock_refresh),
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_set_hvac_mode(HVACMode.OFF)

        # Verify the executor was called once (centralized approach)
        assert mock_executor.call_count == 1
        # async_request_refresh should be called once
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_set_hvac_mode_heat_from_off(hass, mock_coordinator, mock_config_entry):
    """Test setting HVAC mode to heat from off."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.OFF

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Should call: set_power and set_mode together (1 total, centralized approach)
        assert mock_executor.call_count == 1
        # async_request_refresh should be called once
        assert mock_refresh.call_count == 1


@pytest.mark.asyncio
async def test_async_set_hvac_mode_heat_from_on(hass, mock_coordinator, mock_config_entry):
    """Test setting HVAC mode to heat from on."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.ON
    mock_coordinator.data.general.drive_mode = pymitsubishi.DriveMode.COOLER

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Should call set_mode once (centralized approach)
        assert mock_executor.call_count == 1
        # async_request_refresh should be called once
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_set_fan_mode(hass, mock_coordinator, mock_config_entry):
    """Test setting fan mode."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.ON
    mock_coordinator.data.general.drive_mode = pymitsubishi.DriveMode.COOLER
    climate.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_set_fan_mode(FAN_HIGH)

        # Should call set_fan_speed once (centralized approach)
        assert mock_executor.call_count == 1
        # async_request_refresh should be called once for successful commands
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_turn_on(hass, mock_coordinator, mock_config_entry):
    """Test turning on the climate entity."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_turn_on()

        # Should call set_power once (centralized approach)
        assert mock_executor.call_count == 1
        # async_request_refresh should be called once for successful commands
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_turn_off(hass, mock_coordinator, mock_config_entry):
    """Test turning off the climate entity."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_turn_off()

        # Should call set_power once (centralized approach)
        assert mock_executor.call_count == 1
        # async_request_refresh should be called once for successful commands
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_handle_coordinator_update(hass, mock_coordinator, mock_config_entry):
    """Test handling coordinator updates."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)

    with patch.object(climate, "async_write_ha_state") as mock_write_state:
        climate._handle_coordinator_update()
        mock_write_state.assert_called_once()


@pytest.mark.asyncio
async def test_hvac_mode_no_mode_data(hass, mock_coordinator, mock_config_entry):
    """Test hvac_mode property when no mode data is available to cover default return."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data.general = None

    # Should return HVACMode.OFF when no mode data is available
    assert climate.hvac_mode is None


@pytest.mark.asyncio
async def test_async_set_swing_mode_vertical(hass, mock_coordinator, mock_config_entry):
    """Test setting swing mode to vertical."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_set_swing_mode("1")

        # Should call set_vertical_vane once (centralized approach)
        assert mock_executor.call_count == 1

        # async_request_refresh should be called once for successful commands
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_set_horizontal_swing_mode(hass, mock_coordinator, mock_config_entry):
    """Test setting swing mode to horizontal."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await climate.async_set_swing_horizontal_mode("center")

        # Should call set_horizontal_vane once (centralized approach)
        assert mock_executor.call_count == 1

        # async_request_refresh should be called once for successful commands
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.xfail()  # TODO: how do we want to handle this?
async def test_async_set_hvac_mode_power_command_fails(hass, mock_coordinator, mock_config_entry):
    """Test setting HVAC mode when power command fails."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute
    mock_coordinator.data.general.power_on_off = pymitsubishi.PowerOnOff.OFF

    with patch.object(climate, "_execute_command_with_refresh", new=AsyncMock()) as mock_execute:
        # First call (power on) returns False, second call should not happen
        mock_execute.side_effect = requests.exceptions.Timeout()

        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Should only call power command once, mode command should not be called
        assert mock_execute.call_count == 1
        mock_execute.assert_called_with(
            "turn on device before setting mode", mock_coordinator.controller.set_power, True
        )


@pytest.mark.asyncio
@pytest.mark.xfail()  # TODO: how do we want to handle this?
async def test_temperature_command_validation_failure(hass, mock_coordinator, mock_config_entry):
    """Test temperature command when validation fails (device rejects temperature)."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass

    with (
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch("asyncio.sleep", new=AsyncMock()) as mock_sleep,
    ):
        # Mock the command execution to return True (success)
        # Mock get_status_summary to return the "rejected" temperature
        mock_executor.side_effect = [
            True,
            {"target_temp": 20.0},
        ]  # command succeeds, but temp is wrong

        result = await climate._execute_command_with_refresh(
            "set temperature to 25.0°C", mock_coordinator.controller.set_temperature, 25.0
        )

        # Command should still return True but trigger validation failure path
        assert result is True

        # Should have called sleep with 2.0 seconds and refresh due to validation failure
        assert mock_sleep.call_count == 1
        # First call is the standard 2.0 second wait
        mock_sleep.assert_called_with(4.0)
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_command_execution_failure(hass, mock_coordinator, mock_config_entry):
    """Test command execution when the controller command fails."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass

    with patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor:
        # Mock the command to return False (failure)
        mock_executor.return_value = False

        result = await climate._execute_command_with_refresh(
            "test command", mock_coordinator.controller.set_power, True
        )

        # Should return False when command fails
        assert result is False


@pytest.mark.asyncio
async def test_command_execution_exception(hass, mock_coordinator, mock_config_entry):
    """Test command execution when an exception occurs."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass

    with patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor:
        # Mock the command to raise an exception
        mock_executor.side_effect = Exception("Communication error")

        result = await climate._execute_command_with_refresh(
            "test command", mock_coordinator.controller.set_power, True
        )

        # Should return False when exception occurs
        assert result is False


@pytest.mark.asyncio
async def test_temperature_command_validation_success(hass, mock_coordinator, mock_config_entry):
    """Test temperature command when validation succeeds (temperature matches expected)."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass

    # Mock coordinator data to show expected temperature (validation success)
    mock_coordinator.data = {"target_temp": 25.0}  # Device accepted the temperature

    with (
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch("asyncio.sleep", new=AsyncMock()) as mock_sleep,
    ):
        # Mock the command execution to return True (success)
        # Mock get_status_summary to return the expected temperature
        mock_executor.side_effect = [True, {"target_temp": 25.0}]  # command succeeds, temp matches

        result = await climate._execute_command_with_refresh(
            "set temperature to 25.0°C", mock_coordinator.controller.set_temperature, 25.0
        )

        # Command should return True
        assert result is True

        mock_sleep.assert_called_once_with(0.1)
        mock_refresh.assert_called_once()
