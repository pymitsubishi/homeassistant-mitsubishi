"""Tests for the select platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.mitsubishi.const import (
    CONF_EXPERIMENTAL_FEATURES,
    CONF_EXTERNAL_TEMP_ENTITY,
    DOMAIN,
)
from custom_components.mitsubishi.select import (
    MitsubishiPowerSavingSelect,
    MitsubishiTemperatureSourceSelect,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_coordinator, mock_config_entry):
    """Test the setup of Mitsubishi select entities."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], MitsubishiPowerSavingSelect)


@pytest.mark.asyncio
async def test_power_saving_select_init(hass, mock_coordinator, mock_config_entry):
    """Test power saving select entity initialization."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    assert select._attr_name == "Power Saving Mode"
    assert select._attr_icon == "mdi:power-sleep"
    assert select._attr_options == ["Disabled", "Enabled"]
    assert select.unique_id.endswith("_power_saving_select")


@pytest.mark.asyncio
async def test_power_saving_select_current_option_disabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select current option when disabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    assert select.current_option == "Disabled"

    # Test without power saving mode data
    mock_coordinator.data = None
    assert select.current_option is None


@pytest.mark.asyncio
async def test_power_saving_select_async_select_option_enabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select option selection to enabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await select.async_select_option("Enabled")

        # Should call the lambda function wrapping the controller command
        assert mock_executor.call_count == 1
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_power_saving_select_async_select_option_disabled(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select option selection to disabled."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)
    select.hass = hass  # Set hass attribute

    with (
        patch.object(mock_coordinator, "async_request_refresh", new=AsyncMock()) as mock_refresh,
        patch.object(hass, "async_add_executor_job", new=AsyncMock()) as mock_executor,
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        await select.async_select_option("Disabled")

        # Should call the lambda function wrapping the controller command
        assert mock_executor.call_count == 1
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_power_saving_select_extra_state_attributes(
    hass, mock_coordinator, mock_config_entry
):
    """Test power saving select extra state attributes."""
    select = MitsubishiPowerSavingSelect(mock_coordinator, mock_config_entry)

    attributes = select.extra_state_attributes
    assert attributes == {"source": "Mitsubishi AC"}


@pytest.fixture
def mock_config_entry_experimental():
    """Create a mock config entry with experimental features enabled."""
    from homeassistant.const import CONF_HOST
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Mitsubishi AC",
        unique_id="00:11:22:33:44:56",
        data={
            CONF_HOST: "192.168.1.100",
            "encryption_key": "unregistered",
            "admin_username": "admin",
            "admin_password": "password",
            "scan_interval": 30,
        },
        options={
            CONF_EXPERIMENTAL_FEATURES: True,
            CONF_EXTERNAL_TEMP_ENTITY: "sensor.room_temp",
        },
        entry_id="test_entry_exp_id",
    )


@pytest.mark.asyncio
async def test_async_setup_entry_with_experimental(
    hass, mock_coordinator, mock_config_entry_experimental
):
    """Test setup with experimental features enabled creates temperature source select."""
    hass.data[DOMAIN] = {mock_config_entry_experimental.entry_id: mock_coordinator}
    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_config_entry_experimental, async_add_entities)
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 2
    assert isinstance(entities[0], MitsubishiPowerSavingSelect)
    assert isinstance(entities[1], MitsubishiTemperatureSourceSelect)


@pytest.mark.asyncio
async def test_temperature_source_select_init(
    hass, mock_coordinator, mock_config_entry_experimental
):
    """Test temperature source select entity initialization."""
    select = MitsubishiTemperatureSourceSelect(mock_coordinator, mock_config_entry_experimental)

    assert select._attr_name == "Temperature Source"
    assert select._attr_icon == "mdi:thermometer"
    assert select._attr_options == ["Internal", "Remote"]
    assert select.unique_id.endswith("_temperature_source_select")


@pytest.mark.asyncio
async def test_temperature_source_select_current_option_internal(
    hass, mock_coordinator, mock_config_entry_experimental
):
    """Test temperature source select current option when in internal mode."""
    mock_coordinator.remote_temp_mode = False
    select = MitsubishiTemperatureSourceSelect(mock_coordinator, mock_config_entry_experimental)

    assert select.current_option == "Internal"


@pytest.mark.asyncio
async def test_temperature_source_select_current_option_remote(
    hass, mock_coordinator, mock_config_entry_experimental
):
    """Test temperature source select current option when in remote mode."""
    mock_coordinator.remote_temp_mode = True
    select = MitsubishiTemperatureSourceSelect(mock_coordinator, mock_config_entry_experimental)

    assert select.current_option == "Remote"


@pytest.mark.asyncio
async def test_temperature_source_select_switch_to_internal(
    hass, mock_coordinator, mock_config_entry_experimental
):
    """Test switching temperature source to internal."""
    mock_coordinator.set_remote_temp_mode = AsyncMock()
    select = MitsubishiTemperatureSourceSelect(mock_coordinator, mock_config_entry_experimental)
    select.hass = hass
    select.async_write_ha_state = MagicMock()

    await select.async_select_option("Internal")

    # set_remote_temp_mode(False) handles the AC command internally
    mock_coordinator.set_remote_temp_mode.assert_called_once_with(False)
    select.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
async def test_temperature_source_select_switch_to_remote_no_entity(
    hass, mock_coordinator, mock_config_entry
):
    """Test switching to remote fails when no external entity configured."""
    mock_coordinator.set_remote_temp_mode = AsyncMock()
    select = MitsubishiTemperatureSourceSelect(mock_coordinator, mock_config_entry)
    select.hass = hass
    select.async_write_ha_state = MagicMock()

    await select.async_select_option("Remote")

    # Should not change mode when no entity configured
    mock_coordinator.set_remote_temp_mode.assert_not_called()


@pytest.mark.asyncio
async def test_temperature_source_select_extra_state_attributes_no_entity(
    hass, mock_coordinator, mock_config_entry
):
    """Test temperature source select extra state attributes without external entity."""
    select = MitsubishiTemperatureSourceSelect(mock_coordinator, mock_config_entry)
    select.hass = hass

    attributes = select.extra_state_attributes
    assert attributes == {"source": "Mitsubishi AC"}
