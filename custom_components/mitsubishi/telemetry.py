"""Read-only ATA diagnostics from the coordinator's existing status response.

The decoder is owned by pymitsubishi. Older library versions keep their existing
entities and return no additional telemetry entities. No requests are sent here.
"""

from __future__ import annotations

from typing import Any

import pymitsubishi
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfFrequency
from homeassistant.helpers.entity import EntityCategory

from .coordinator import MitsubishiDataUpdateCoordinator
from .entity import MitsubishiEntity

REFERENCE = "https://muart-group.github.io/developer/it-protocol"

# Existing sensors retain their IDs and interpretation. New raw/candidate fields
# are diagnostics and disabled by default; timer bytes deliberately have no unit.
SENSOR_FIELDS = (
    "compressor_frequency",
    "status_flags",
    "actual_fan_code",
    "remote_lock_flags",
    "error_display_code_raw",
    "error_display_code",
    "timer_mode_code",
    "timer_on_set_raw",
    "timer_off_set_raw",
    "timer_on_remaining_raw",
    "timer_off_remaining_raw",
    "airflow_control_code",
    "left_vertical_vane_raw",
    "auto_mode_raw",
    "auto_mode_code",
    "horizontal_vane_extra_flags",
)
FLAG_FIELDS = (
    "defrost_reported",
    "preheat_reported",
    "standby_reported",
    "filter_reported",
    "power_locked",
    "mode_locked",
    "temperature_locked",
    "auto_leader_candidate",
)


class TelemetryEntity(MitsubishiEntity):
    """A field that is unavailable when its current packet is invalid or absent."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: MitsubishiDataUpdateCoordinator, entry: ConfigEntry, field: str
    ) -> None:
        super().__init__(coordinator, entry, f"telemetry_{field}")
        self.field = field
        self._attr_translation_key = f"telemetry_{field}"

    @property
    def snapshot(self) -> Any:
        """Use the parsed snapshot, never a separate request or cached last value."""
        return getattr(self.coordinator.data, "ata_telemetry", None)

    @property
    def available(self) -> bool:
        snapshot = self.snapshot
        info = getattr(pymitsubishi, "FIELD_INFO", {}).get(self.field)
        return bool(
            super().available
            and snapshot is not None
            and info is not None
            and snapshot.group_quality.get(f"0x{info.group:02X}") == "valid"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        info = getattr(pymitsubishi, "FIELD_INFO", {}).get(self.field)
        if info is None:
            return {}
        return {
            "group": f"0x{info.group:02X}",
            "payload_offsets": list(info.offsets),
            "confidence": info.confidence,
            "protocol_reference": REFERENCE,
        }


class TelemetrySensor(TelemetryEntity, SensorEntity):
    """An additional raw code or documented numeric measurement."""

    def __init__(
        self, coordinator: MitsubishiDataUpdateCoordinator, entry: ConfigEntry, field: str
    ) -> None:
        super().__init__(coordinator, entry, field)
        if field == "compressor_frequency":
            self._attr_device_class = SensorDeviceClass.FREQUENCY
            self._attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | float | str | None:
        snapshot = self.snapshot
        return snapshot.value(self.field) if snapshot is not None else None


class TelemetryFlag(TelemetryEntity, BinarySensorEntity):
    """A reported status bit; missing data does not become false."""

    @property
    def is_on(self) -> bool | None:
        value = self.snapshot.value(self.field) if self.snapshot is not None else None
        return value if isinstance(value, bool) else None


class TelemetryOverview(TelemetryEntity, SensorEntity):
    """Packet quality and decoded values without full changing raw frames."""

    _attr_icon = "mdi:code-json"

    def __init__(self, coordinator: MitsubishiDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "overview")

    @property
    def available(self) -> bool:
        return super(TelemetryEntity, self).available and self.snapshot is not None

    @property
    def native_value(self) -> int | None:
        return sum(f.valid for f in self.snapshot.frames) if self.snapshot is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snapshot = self.snapshot
        if snapshot is None:
            return {}
        return {
            "group_quality": snapshot.group_quality,
            "values": snapshot.values,
            "unknown_bytes": snapshot.unknown_bytes,
            "protocol_reference": REFERENCE,
            "candidate_fields": [
                name
                for name in snapshot.values
                if getattr(pymitsubishi, "FIELD_INFO", {})[name].confidence == "candidate"
            ],
        }


def telemetry_sensors(
    coordinator: MitsubishiDataUpdateCoordinator, entry: ConfigEntry
) -> list[SensorEntity]:
    """Allow a dependency-first rollout without requiring an unreleased version."""
    if getattr(coordinator.data, "ata_telemetry", None) is None:
        return []
    return [
        TelemetryOverview(coordinator, entry),
        *[TelemetrySensor(coordinator, entry, key) for key in SENSOR_FIELDS],
    ]


def telemetry_binary_sensors(
    coordinator: MitsubishiDataUpdateCoordinator, entry: ConfigEntry
) -> list[BinarySensorEntity]:
    """Return read-only flags without changing control or capability detection."""
    if getattr(coordinator.data, "ata_telemetry", None) is None:
        return []
    return [TelemetryFlag(coordinator, entry, key) for key in FLAG_FIELDS]
