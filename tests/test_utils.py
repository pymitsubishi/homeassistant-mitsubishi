"""Test the utils module."""

from unittest.mock import MagicMock

import pytest

from custom_components.mitsubishi.utils import (
    filter_none_values,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with controller state structure."""
    coordinator = MagicMock()
    coordinator.controller = MagicMock()
    coordinator.controller.state = MagicMock()
    return coordinator


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
