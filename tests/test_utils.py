"""Test the utils module."""

from unittest.mock import MagicMock

import pytest

from custom_components.mitsubishi.utils import (
    filter_none_values,
    get_energy_state_attributes,
    get_general_state_attributes,
    has_controller_state,
    has_energy_state,
    has_general_state,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with controller state structure."""
    coordinator = MagicMock()
    coordinator.controller = MagicMock()
    coordinator.controller.state = MagicMock()
    return coordinator


def test_has_controller_state_valid(mock_coordinator):
    """Test has_controller_state with valid coordinator."""
    assert has_controller_state(mock_coordinator) is True


def test_has_controller_state_no_controller():
    """Test has_controller_state with no controller attribute."""
    coordinator = MagicMock()
    del coordinator.controller
    assert has_controller_state(coordinator) is False


def test_has_controller_state_no_state():
    """Test has_controller_state with no state attribute."""
    coordinator = MagicMock()
    coordinator.controller = MagicMock()
    del coordinator.controller.state
    assert has_controller_state(coordinator) is False


def test_has_controller_state_none_state():
    """Test has_controller_state with None state."""
    coordinator = MagicMock()
    coordinator.controller = MagicMock()
    coordinator.controller.state = None
    assert has_controller_state(coordinator) is False


def test_has_energy_state_valid(mock_coordinator):
    """Test has_energy_state with valid energy state."""
    mock_coordinator.controller.state.energy = MagicMock()
    assert has_energy_state(mock_coordinator) is True


def test_has_energy_state_no_energy(mock_coordinator):
    """Test has_energy_state with no energy attribute."""
    del mock_coordinator.controller.state.energy
    assert has_energy_state(mock_coordinator) is False


def test_has_energy_state_none_energy(mock_coordinator):
    """Test has_energy_state with None energy."""
    mock_coordinator.controller.state.energy = None
    assert has_energy_state(mock_coordinator) is False


def test_has_general_state_valid(mock_coordinator):
    """Test has_general_state with valid general state."""
    mock_coordinator.controller.state.general = MagicMock()
    assert has_general_state(mock_coordinator) is True


def test_has_general_state_no_general(mock_coordinator):
    """Test has_general_state with no general attribute."""
    del mock_coordinator.controller.state.general
    assert has_general_state(mock_coordinator) is False


def test_has_general_state_none_general(mock_coordinator):
    """Test has_general_state with None general."""
    mock_coordinator.controller.state.general = None
    assert has_general_state(mock_coordinator) is False


def test_get_energy_state_attributes_valid(mock_coordinator):
    """Test get_energy_state_attributes with valid energy state."""
    mock_energy = MagicMock()
    mock_energy.operating = True
    mock_energy.compressor_frequency = 60
    mock_coordinator.controller.state.energy = mock_energy

    result = get_energy_state_attributes(mock_coordinator)
    expected = {
        "operating_status": True,
        "compressor_frequency": 60,
    }
    assert result == expected


def test_get_energy_state_attributes_no_energy(mock_coordinator):
    """Test get_energy_state_attributes with no energy state."""
    del mock_coordinator.controller.state.energy
    result = get_energy_state_attributes(mock_coordinator)
    assert result == {}


def test_get_general_state_attributes_valid(mock_coordinator):
    """Test get_general_state_attributes with valid general state."""
    mock_general = MagicMock()
    mock_general.mode_raw_value = 15
    mock_general.drive_mode = MagicMock()
    mock_general.drive_mode.name = "cool"
    mock_general.i_see_sensor = True
    mock_general.wide_vane_adjustment = False
    mock_coordinator.controller.state.general = mock_general

    result = get_general_state_attributes(mock_coordinator)
    expected = {
        "mode_raw_value": "0x0f",
        "parsed_mode": "cool",
        "i_see_sensor_active": True,
        "wide_vane_adjustment": False,
    }
    assert result == expected


def test_get_general_state_attributes_no_general(mock_coordinator):
    """Test get_general_state_attributes with no general state."""
    del mock_coordinator.controller.state.general
    result = get_general_state_attributes(mock_coordinator)
    assert result == {}


def test_get_general_state_attributes_none_mode_raw_value(mock_coordinator):
    """Test get_general_state_attributes with None mode_raw_value."""
    mock_general = MagicMock()
    mock_general.mode_raw_value = None
    mock_general.drive_mode = None
    mock_general.i_see_sensor = False
    mock_general.wide_vane_adjustment = True
    mock_coordinator.controller.state.general = mock_general

    result = get_general_state_attributes(mock_coordinator)
    expected = {
        "i_see_sensor_active": False,
        "wide_vane_adjustment": True,
    }
    assert result == expected


def test_filter_none_values():
    """Test filter_none_values function."""
    input_dict = {
        "key1": "value1",
        "key2": None,
        "key3": 42,
        "key4": None,
        "key5": False,
        "key6": 0,
        "key7": "",
    }
    result = filter_none_values(input_dict)
    expected = {
        "key1": "value1",
        "key3": 42,
        "key5": False,
        "key6": 0,
        "key7": "",
    }
    assert result == expected


def test_filter_none_values_empty():
    """Test filter_none_values with empty dict."""
    result = filter_none_values({})
    assert result == {}


def test_filter_none_values_all_none():
    """Test filter_none_values with all None values."""
    input_dict = {"key1": None, "key2": None}
    result = filter_none_values(input_dict)
    assert result == {}
