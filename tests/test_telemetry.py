"""Protocol diagnostics using only simulated coordinator data, never a device."""

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pymitsubishi
import pytest

from custom_components.mitsubishi.diagnostics import async_get_config_entry_diagnostics
from custom_components.mitsubishi.telemetry import telemetry_binary_sensors, telemetry_sensors


def packet(group, changes=None):
    payload = bytearray(16)
    payload[0] = group
    for offset, value in (changes or {}).items():
        payload[offset] = value
    result = bytearray([0xFC, 0x62, 1, 0x30, 16]) + payload
    result.append((-sum(result[1:])) & 255)
    return result.hex()


def setup_entities(values):
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = SimpleNamespace(
        mac="00:11:22:33:44:55",
        serial="private-serial",
        ata_telemetry=pymitsubishi.parse_ata_telemetry(values),
    )
    entry = SimpleNamespace(
        data={"host": "192.0.2.1", "password": "private-password"}, entry_id="test"
    )
    sensors = telemetry_sensors(coordinator, entry)
    flags = telemetry_binary_sensors(coordinator, entry)
    return coordinator, entry, sensors, flags


def test_legacy_dependency_adds_no_entities():
    coordinator = SimpleNamespace(data=SimpleNamespace())
    assert telemetry_sensors(coordinator, None) == []
    assert telemetry_binary_sensors(coordinator, None) == []


@pytest.mark.skipif(
    not hasattr(pymitsubishi, "parse_ata_telemetry"),
    reason="Requires the companion pymitsubishi telemetry PR",
)
def test_reported_bits_missing_data_and_offline_state():
    coordinator, _, sensors, flags = setup_entities([packet(9, {3: 2, 4: 3}), packet(6, {3: 47})])
    by_field = {e.field: e for e in flags}
    assert by_field["defrost_reported"].is_on is True
    assert by_field["preheat_reported"].is_on is False
    assert not by_field["power_locked"].available
    frequency = next(e for e in sensors if e.field == "compressor_frequency")
    assert frequency.native_value == 47
    assert frequency.native_unit_of_measurement == "Hz"
    assert by_field["defrost_reported"].extra_state_attributes["confidence"] == "documented"
    assert all(not e.entity_registry_enabled_default for e in [*sensors, *flags])
    assert len({e.unique_id for e in [*sensors, *flags]}) == len(sensors) + len(flags)
    coordinator.data.ata_telemetry = pymitsubishi.parse_ata_telemetry([])
    assert by_field["defrost_reported"].is_on is None
    assert not by_field["defrost_reported"].available
    assert sensors[0].available and sensors[0].native_value == 0
    coordinator.last_update_success = False
    assert not any(e.available for e in [*sensors, *flags])
    coordinator.controller.api.send_status_request.assert_not_called()


@pytest.mark.skipif(
    not hasattr(pymitsubishi, "parse_ata_telemetry"),
    reason="Requires the companion pymitsubishi telemetry PR",
)
@pytest.mark.parametrize("raw", [packet(9)[:-2] + "00", packet(9)[:-2]])
def test_malformed_frame_does_not_become_false(raw):
    _, _, _, flags = setup_entities([raw])
    defrost = next(e for e in flags if e.field == "defrost_reported")
    assert not defrost.available
    assert defrost.is_on is None


@pytest.mark.skipif(
    not hasattr(pymitsubishi, "parse_ata_telemetry"),
    reason="Requires the companion pymitsubishi telemetry PR",
)
def test_timer_raw_bytes_and_sanitized_diagnostics():
    coordinator, entry, sensors, _ = setup_entities([packet(5, {4: 9}), packet(9)])
    timer = next(e for e in sensors if e.field == "timer_on_set_raw")
    assert timer.native_value == 9
    assert timer.native_unit_of_measurement is None
    assert timer.extra_state_attributes["confidence"] == "candidate"
    hass = SimpleNamespace(data={"mitsubishi": {entry.entry_id: coordinator}})
    diagnostic = asyncio.run(async_get_config_entry_diagnostics(hass, entry))
    assert diagnostic["ata_telemetry"]["frames"][0]["raw"] == packet(5, {4: 9})
    assert "private" not in str(diagnostic)
    assert "192.0.2.1" not in str(diagnostic)
    assert "00:11:22:33:44:55" not in str(diagnostic)
