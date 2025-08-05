"""Tests for the climate platform."""
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_VERTICAL,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.mitsubishi.climate import (
    MitsubishiClimate,
    async_setup_entry,
)
from custom_components.mitsubishi.const import DOMAIN


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
    mock_coordinator.data = {"mac": "00:11:22:33:44:55"}
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)

    assert climate._config_entry == mock_config_entry
    assert climate.unique_id == "00:11:22:33:44:55_climate"


@pytest.mark.asyncio
async def test_current_temperature(hass, mock_coordinator, mock_config_entry):
    """Test current temperature property."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)

    # Test with temperature data
    mock_coordinator.data = {"room_temp": 22.5}
    assert climate.current_temperature == 22.5

    # Test without temperature data
    mock_coordinator.data = {}
    assert climate.current_temperature is None


@pytest.mark.asyncio
async def test_target_temperature(hass, mock_coordinator, mock_config_entry):
    """Test target temperature property."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)

    # Test with target temperature data
    mock_coordinator.data = {"target_temp": 24.0}
    assert climate.target_temperature == 24.0

    # Test without target temperature data
    mock_coordinator.data = {}
    assert climate.target_temperature is None


@pytest.mark.asyncio
async def test_hvac_mode_off(hass, mock_coordinator, mock_config_entry):
    """Test HVAC mode when power is off."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"power": "OFF"}
    assert climate.hvac_mode == HVACMode.OFF


@pytest.mark.asyncio
async def test_hvac_mode_heat(hass, mock_coordinator, mock_config_entry):
    """Test HVAC mode when set to heat."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"power": "ON", "mode": "HEATER"}
    assert climate.hvac_mode == HVACMode.HEAT


@pytest.mark.asyncio
async def test_hvac_mode_cool(hass, mock_coordinator, mock_config_entry):
    """Test HVAC mode when set to cool."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"power": "ON", "mode": "COOLER"}
    assert climate.hvac_mode == HVACMode.COOL


@pytest.mark.asyncio
async def test_hvac_mode_auto(hass, mock_coordinator, mock_config_entry):
    """Test HVAC mode when set to auto."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"power": "ON", "mode": "AUTO"}
    assert climate.hvac_mode == HVACMode.AUTO


@pytest.mark.asyncio
async def test_hvac_mode_invalid(hass, mock_coordinator, mock_config_entry):
    """Test HVAC mode with invalid data."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"power": "ON", "mode": "INVALID"}
    assert climate.hvac_mode == HVACMode.OFF


@pytest.mark.asyncio
async def test_hvac_action_off(hass, mock_coordinator, mock_config_entry):
    """Test HVAC action when power is off."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"power": "OFF"}
    assert climate.hvac_action == HVACAction.OFF


@pytest.mark.asyncio
async def test_hvac_action_heating(hass, mock_coordinator, mock_config_entry):
    """Test HVAC action when heating."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"power": "ON", "mode": "HEATER"}
    assert climate.hvac_action == HVACAction.HEATING


@pytest.mark.asyncio
async def test_hvac_action_cooling(hass, mock_coordinator, mock_config_entry):
    """Test HVAC action when cooling."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"power": "ON", "mode": "COOLER"}
    assert climate.hvac_action == HVACAction.COOLING


@pytest.mark.asyncio
async def test_fan_mode_auto(hass, mock_coordinator, mock_config_entry):
    """Test fan mode when set to auto."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"fan_speed": "AUTO"}
    assert climate.fan_mode == FAN_AUTO


@pytest.mark.asyncio
async def test_fan_mode_low(hass, mock_coordinator, mock_config_entry):
    """Test fan mode when set to low."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"fan_speed": "LEVEL_1"}
    assert climate.fan_mode == FAN_LOW


@pytest.mark.asyncio
async def test_fan_mode_invalid(hass, mock_coordinator, mock_config_entry):
    """Test fan mode with invalid data."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {"fan_speed": "INVALID"}
    assert climate.fan_mode == FAN_AUTO


@pytest.mark.asyncio
async def test_swing_mode(hass, mock_coordinator, mock_config_entry):
    """Test swing mode (currently always returns OFF)."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    assert climate.swing_mode == SWING_OFF


@pytest.mark.asyncio
async def test_extra_state_attributes(hass, mock_coordinator, mock_config_entry):
    """Test extra state attributes."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {
        "outside_temp": 18.0,
        "power_saving_mode": True,
        "dehumidifier_setting": 50,
        "error_code": "8000",
        "abnormal_state": True,  # Changed to True so it gets added
        "capabilities": {"heating": True, "cooling": True},
    }

    attributes = climate.extra_state_attributes
    assert attributes["outdoor_temperature"] == 18.0
    assert attributes["power_saving_mode"] is True
    assert attributes["dehumidifier_setting"] == 50
    assert attributes["error_code"] == "8000"
    assert attributes["abnormal_state"] is True  # Updated assertion
    assert attributes["supported_modes"] == ["heating", "cooling"]


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
    with patch.object(mock_coordinator.controller, "set_temperature"), mock_async_methods(
        hass, mock_coordinator
    ) as (mock_executor, mock_refresh), patch("asyncio.sleep", new=AsyncMock()):
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

    with mock_async_methods(hass, mock_coordinator) as (mock_executor, mock_refresh), patch(
        "asyncio.sleep", new=AsyncMock()
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
    mock_coordinator.data = {"power": "OFF"}  # Currently off

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Should call: set_power and set_mode (2 total, centralized approach)
        assert mock_executor.call_count == 2
        # async_request_refresh should be called twice
        assert mock_refresh.call_count == 2


@pytest.mark.asyncio
async def test_async_set_hvac_mode_heat_from_on(hass, mock_coordinator, mock_config_entry):
    """Test setting HVAC mode to heat from on."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute
    mock_coordinator.data = {"power": "ON", "mode": "COOLER"}  # Currently on

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Should call set_mode once (centralized approach)
        assert mock_executor.call_count == 1
        # async_request_refresh should be called once
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_set_fan_mode(hass, mock_coordinator, mock_config_entry):
    """Test setting fan mode."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
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

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
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

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
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
async def test_hvac_mode_with_invalid_drive_mode(hass, mock_coordinator, mock_config_entry):
    """Test hvac_mode property with invalid drive mode to cover exception handling."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {
        "power": "ON",
        "mode": "INVALID_MODE",  # This will cause KeyError in DriveMode[mode_name]
    }

    # Should return HVACMode.OFF when KeyError occurs
    assert climate.hvac_mode == HVACMode.OFF


@pytest.mark.asyncio
async def test_hvac_mode_no_mode_data(hass, mock_coordinator, mock_config_entry):
    """Test hvac_mode property when no mode data is available to cover default return."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {
        "power": "ON",
        # No "mode" key to trigger the default return at line 164
    }

    # Should return HVACMode.OFF when no mode data is available
    assert climate.hvac_mode == HVACMode.OFF


@pytest.mark.asyncio
async def test_hvac_action_with_invalid_drive_mode(hass, mock_coordinator, mock_config_entry):
    """Test hvac_action property with invalid drive mode to cover exception handling."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)

    # Mock hvac_mode to not return OFF so we can reach the exception in hvac_action
    with patch.object(type(climate), "hvac_mode", new_callable=PropertyMock) as mock_hvac_mode:
        mock_hvac_mode.return_value = HVACMode.HEAT
        mock_coordinator.data = {
            "power": "ON",
            "mode": "INVALID_MODE",  # This will cause KeyError in DriveMode[mode_name]
        }

        # Should return HVACAction.IDLE when KeyError occurs in hvac_action
        assert climate.hvac_action == HVACAction.IDLE


@pytest.mark.asyncio
async def test_async_set_swing_mode_vertical(hass, mock_coordinator, mock_config_entry):
    """Test setting swing mode to vertical."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
        await climate.async_set_swing_mode(SWING_VERTICAL)

        # Should call set_vertical_vane once (centralized approach)
        assert mock_executor.call_count == 1

        # async_request_refresh should be called once for successful commands
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_set_swing_mode_horizontal(hass, mock_coordinator, mock_config_entry):
    """Test setting swing mode to horizontal."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
        await climate.async_set_swing_mode(SWING_HORIZONTAL)

        # Should call set_horizontal_vane once (centralized approach)
        assert mock_executor.call_count == 1

        # async_request_refresh should be called once for successful commands
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_set_swing_mode_both(hass, mock_coordinator, mock_config_entry):
    """Test setting swing mode to both vertical and horizontal."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch("asyncio.sleep", new=AsyncMock()):
        await climate.async_set_swing_mode(SWING_BOTH)

        # Should call both vane methods twice (centralized approach, two commands)
        assert mock_executor.call_count == 2

        # async_request_refresh should be called twice for two successful commands
        assert mock_refresh.call_count == 2


@pytest.mark.asyncio
async def test_async_set_swing_mode_off(hass, mock_coordinator, mock_config_entry):
    """Test setting swing mode to off (no action taken in current implementation)."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute

    with patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor:
        await climate.async_set_swing_mode(SWING_OFF)

        # For SWING_OFF, no controller methods should be called in current implementation
        mock_executor.assert_not_called()

        # No refresh should be called since no command was executed
        mock_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_hvac_action_idle_when_not_operating(hass, mock_coordinator, mock_config_entry):
    """Test HVAC action returns IDLE when compressor is not operating."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {
        "power": "ON",
        "mode": "HEATER",
        "energy_states": {
            "operating": False  # Compressor not running
        },
    }
    assert climate.hvac_action == HVACAction.IDLE


@pytest.mark.asyncio
async def test_hvac_action_based_on_mode_when_operating(hass, mock_coordinator, mock_config_entry):
    """Test HVAC action based on mode when compressor is operating."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {
        "power": "ON",
        "mode": "HEATER",
        "energy_states": {
            "operating": True  # Compressor running
        },
    }
    assert climate.hvac_action == HVACAction.HEATING


@pytest.mark.asyncio
async def test_hvac_action_no_energy_states(hass, mock_coordinator, mock_config_entry):
    """Test HVAC action when no energy states available."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {
        "power": "ON",
        "mode": "COOLER",
        # No energy_states
    }
    assert climate.hvac_action == HVACAction.COOLING


@pytest.mark.asyncio
async def test_extra_state_attributes_with_energy_states(hass, mock_coordinator, mock_config_entry):
    """Test extra state attributes includes energy state data."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    mock_coordinator.data = {
        "energy_states": {
            "compressor_frequency": 42.5,
            "operating": True,
            "estimated_power_watts": 850,
        }
    }

    attributes = climate.extra_state_attributes
    assert attributes["compressor_frequency"] == 42.5
    assert attributes["compressor_operating"] is True
    assert attributes["estimated_power_watts"] == 850


@pytest.mark.asyncio
async def test_async_set_hvac_mode_power_command_fails(hass, mock_coordinator, mock_config_entry):
    """Test setting HVAC mode when power command fails."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass  # Set hass attribute
    mock_coordinator.data = {"power": "OFF"}  # Currently off

    with patch.object(climate, "_execute_command_with_refresh", new=AsyncMock()) as mock_execute:
        # First call (power on) returns False, second call should not happen
        mock_execute.return_value = False

        await climate.async_set_hvac_mode(HVACMode.HEAT)

        # Should only call power command once, mode command should not be called
        assert mock_execute.call_count == 1
        mock_execute.assert_called_with(
            "turn on device before setting mode", mock_coordinator.controller.set_power, True
        )


@pytest.mark.asyncio
async def test_update_coordinator_from_controller_state_success(
    hass, mock_coordinator, mock_config_entry
):
    """Test successful update of coordinator from controller state."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass

    summary = {"target_temp": 22.0}  # Mocked status summary

    with patch.object(
        hass, "async_add_executor_job", new=AsyncMock(return_value=summary)
    ), patch.object(
        mock_coordinator, "async_update_listeners", new=AsyncMock()
    ) as mock_update_listeners:
        await climate._update_coordinator_from_controller_state()

        # Assert that the data was set correctly
        assert climate.coordinator.data == summary

        # Ensure that the update listeners function was called
        mock_update_listeners.assert_called_once()


@pytest.mark.asyncio
async def test_temperature_command_validation_failure(hass, mock_coordinator, mock_config_entry):
    """Test temperature command when validation fails (device rejects temperature)."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass

    # Mock coordinator data to show different temperature than expected
    mock_coordinator.data = {"target_temp": 20.0}  # Device rejected and kept old temp

    with patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
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
        mock_sleep.assert_called_with(2.0)
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
async def test_update_coordinator_from_controller_state_exception(
    hass, mock_coordinator, mock_config_entry
):
    """Test _update_coordinator_from_controller_state when exception occurs."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass

    with patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh:
        # Mock get_status_summary to raise an exception
        mock_executor.side_effect = Exception("Controller error")

        await climate._update_coordinator_from_controller_state()

        # Should fall back to regular refresh when exception occurs
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_temperature_command_validation_success(hass, mock_coordinator, mock_config_entry):
    """Test temperature command when validation succeeds (temperature matches expected)."""
    climate = MitsubishiClimate(mock_coordinator, mock_config_entry)
    climate.hass = hass

    # Mock coordinator data to show expected temperature (validation success)
    mock_coordinator.data = {"target_temp": 25.0}  # Device accepted the temperature

    with patch.object(
        hass, "async_add_executor_job", new=AsyncMock()
    ) as mock_executor, patch.object(
        mock_coordinator, "async_request_refresh", new=AsyncMock()
    ) as mock_refresh, patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        # Mock the command execution to return True (success)
        # Mock get_status_summary to return the expected temperature
        mock_executor.side_effect = [True, {"target_temp": 25.0}]  # command succeeds, temp matches

        result = await climate._execute_command_with_refresh(
            "set temperature to 25.0°C", mock_coordinator.controller.set_temperature, 25.0
        )

        # Command should return True
        assert result is True

        # Should have called sleep with 2.0 seconds (standard wait) and refresh
        mock_sleep.assert_called_once_with(2.0)
        mock_refresh.assert_called_once()
