"""Utility functions for the Mitsubishi integration to reduce code duplication."""

from typing import Any


def filter_none_values(attributes: dict[str, Any]) -> dict[str, Any]:
    """Filter out None values from attributes dictionary."""
    return {k: v for k, v in attributes.items() if v is not None}
