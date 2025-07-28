"""Utility functions for the Mitsubishi integration to reduce code duplication."""

from typing import Any


def has_controller_state(coordinator: Any) -> bool:
    """Check if coordinator has a valid controller state."""
    return (
        hasattr(coordinator, "controller")
        and hasattr(coordinator.controller, "state")
        and coordinator.controller.state is not None
    )


def has_energy_state(coordinator: Any) -> bool:
    """Check if coordinator has a valid energy state."""
    return (
        has_controller_state(coordinator)
        and hasattr(coordinator.controller.state, "energy")
        and coordinator.controller.state.energy is not None
    )


def has_general_state(coordinator: Any) -> bool:
    """Check if coordinator has a valid general state."""
    return (
        has_controller_state(coordinator)
        and hasattr(coordinator.controller.state, "general")
        and coordinator.controller.state.general is not None
    )


def get_energy_state_attributes(coordinator: Any) -> dict[str, Any]:
    """Get common energy state attributes."""
    attrs = {}
    if has_energy_state(coordinator):
        energy = coordinator.controller.state.energy
        attrs["operating_status"] = energy.operating
        attrs["compressor_frequency"] = energy.compressor_frequency
    return attrs


def get_general_state_attributes(coordinator: Any) -> dict[str, Any]:
    """Get common general state attributes."""
    attrs = {}
    if has_general_state(coordinator):
        general = coordinator.controller.state.general
        if general.mode_raw_value is not None:
            attrs["mode_raw_value"] = f"0x{general.mode_raw_value:02x}"
        if general.drive_mode:
            attrs["parsed_mode"] = general.drive_mode.name
        attrs["i_see_sensor_active"] = general.i_see_sensor
        attrs["wide_vane_adjustment"] = general.wide_vane_adjustment
    return attrs


def filter_none_values(attributes: dict[str, Any]) -> dict[str, Any]:
    """Filter out None values from attributes dictionary."""
    return {k: v for k, v in attributes.items() if v is not None}
