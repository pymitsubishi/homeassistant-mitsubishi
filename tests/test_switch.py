"""Tests for the Mitsubishi cloud connection switch."""

import dataclasses
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import EntityCategory
from pymitsubishi import ParsedDeviceState

from custom_components.mitsubishi.const import DOMAIN
from custom_components.mitsubishi.switch import (
    MitsubishiCloudConnectionSwitch,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_coordinator, mock_config_entry):
    """Test the setup of the Mitsubishi switch entities."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], MitsubishiCloudConnectionSwitch)


@pytest.mark.asyncio
async def test_switch_init(hass, mock_coordinator, mock_config_entry):
    """Test cloud connection switch initialization."""
    switch = MitsubishiCloudConnectionSwitch(mock_coordinator, mock_config_entry)

    assert switch._attr_name == "MELCloud connection"
    assert switch._attr_icon == "mdi:cloud-outline"
    assert switch._attr_device_class == SwitchDeviceClass.SWITCH
    assert switch._attr_entity_category == EntityCategory.CONFIG
    assert switch.unique_id.endswith("_cloud_connection")


@pytest.mark.asyncio
@pytest.mark.parametrize("reported", [True, False])
async def test_is_on_follows_the_adapter(hass, mock_coordinator, mock_config_entry, reported):
    """The switch reports whatever setting the adapter last returned."""
    mock_coordinator.data.cloud_connect = reported
    switch = MitsubishiCloudConnectionSwitch(mock_coordinator, mock_config_entry)

    assert switch.is_on is reported


@pytest.mark.asyncio
async def test_unavailable_until_the_adapter_reports(hass, mock_coordinator, mock_config_entry):
    """Before the first status fetch the setting is unknown."""
    mock_coordinator.data.cloud_connect = None
    switch = MitsubishiCloudConnectionSwitch(mock_coordinator, mock_config_entry)

    assert switch.available is False


@pytest.mark.asyncio
async def test_available_once_reported(hass, mock_coordinator, mock_config_entry):
    """Test availability once the adapter has reported the setting."""
    mock_coordinator.data.cloud_connect = True
    switch = MitsubishiCloudConnectionSwitch(mock_coordinator, mock_config_entry)

    assert switch.available is True


@pytest.mark.asyncio
async def test_turn_on_enables_the_connection(hass, mock_coordinator, mock_config_entry):
    """Test turning the cloud connection on."""
    switch = MitsubishiCloudConnectionSwitch(mock_coordinator, mock_config_entry)

    with patch.object(switch, "_execute_command_with_refresh", AsyncMock()) as execute:
        await switch.async_turn_on()

    execute.assert_called_once_with(
        "enable MELCloud connection",
        mock_coordinator.controller.set_cloud_connect,
        True,
    )


@pytest.mark.asyncio
async def test_turn_off_disables_the_connection(hass, mock_coordinator, mock_config_entry):
    """Test turning the cloud connection off."""
    switch = MitsubishiCloudConnectionSwitch(mock_coordinator, mock_config_entry)

    with patch.object(switch, "_execute_command_with_refresh", AsyncMock()) as execute:
        await switch.async_turn_off()

    execute.assert_called_once_with(
        "disable MELCloud connection",
        mock_coordinator.controller.set_cloud_connect,
        False,
    )


def test_library_exposes_the_cloud_setting():
    """The switch reads cloud_connect off the parsed state, so the pinned library must carry it."""
    assert "cloud_connect" in {f.name for f in dataclasses.fields(ParsedDeviceState)}
