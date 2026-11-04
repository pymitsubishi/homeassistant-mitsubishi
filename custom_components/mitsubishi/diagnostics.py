"""Sanitized protocol diagnostics, excluding adapter identity and configuration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return only framed protocol data; never credentials, IP, MAC or XML."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    snapshot = getattr(coordinator.data, "ata_telemetry", None)
    return {
        "last_update_success": coordinator.last_update_success,
        "ata_telemetry": snapshot.to_dict() if snapshot is not None else None,
    }
