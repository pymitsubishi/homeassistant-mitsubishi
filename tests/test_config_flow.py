"""Test the Mitsubishi Air Conditioner config flow."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.mitsubishi.const import DOMAIN


@pytest.fixture
def mock_api():
    """Create a mock MitsubishiAPI."""
    api = MagicMock()
    api.device_ip = "192.168.1.100"
    api.admin_user = "admin"
    api.admin_password = "password"
    return api


@pytest.fixture
def mock_controller():
    """Create a mock MitsubishiController."""
    controller = MagicMock()
    controller.fetch_status.return_value = True
    controller.get_status_summary.return_value = {
        "power": "on",
        "target_temp": 24.0,
        "room_temp": 22.5,
        "mode": "cool",
        "fan_speed": "auto",
        "device_info": {
            "model": "MAC-577IF-2E",
            "firmware": "1.0.0",
            "mac_address": "AA:BB:CC:DD:EE:FF"
        }
    }
    return controller


class TestConfigFlow:
    """Test the config flow for Mitsubishi Air Conditioner."""

    async def test_form(self, hass: HomeAssistant) -> None:
        """Test we get the form."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_form_invalid_host(self, hass: HomeAssistant) -> None:
        """Test we handle invalid host."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.mitsubishi.config_flow.MitsubishiAPI"
        ) as mock_api_class:
            mock_api = MagicMock()
            mock_api_class.return_value = mock_api

            with patch(
                "custom_components.mitsubishi.config_flow.MitsubishiController"
            ) as mock_controller_class:
                mock_controller = MagicMock()
                mock_controller.fetch_status.return_value = False
                mock_controller_class.return_value = mock_controller

                result2 = await hass.config_entries.flow.async_configure(
                    result["flow_id"],
                    {"host": "192.168.1.100"},
                )

                assert result2["type"] == FlowResultType.FORM
                assert result2["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_form_success(self, hass: HomeAssistant, mock_api, mock_controller) -> None:
        """Test successful configuration."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.mitsubishi.config_flow.MitsubishiAPI"
        ) as mock_api_class:
            mock_api_class.return_value = mock_api

            with patch(
                "custom_components.mitsubishi.config_flow.MitsubishiController"
            ) as mock_controller_class:
                mock_controller_class.return_value = mock_controller

                result2 = await hass.config_entries.flow.async_configure(
                    result["flow_id"],
                    {
                        "host": "192.168.1.100",
                        "admin_username": "admin",
                        "admin_password": "password",
                        "scan_interval": 30,
                    },
                )

                assert result2["type"] == FlowResultType.CREATE_ENTRY
                assert result2["title"] == "Mitsubishi AC (192.168.1.100)"
                assert result2["data"] == {
                    "host": "192.168.1.100",
                    "admin_username": "admin",
                    "admin_password": "password",
                    "scan_interval": 30,
                    "encryption_key": "unregistered",
                    "enable_capability_detection": True,
                }

    @pytest.mark.asyncio
    async def test_form_already_configured(self, hass: HomeAssistant) -> None:
        """Test we handle already configured."""
        # Mock the entry creation first, but don't add it yet
        with patch(
            "custom_components.mitsubishi.config_flow.MitsubishiAPI"
        ) as mock_api_class:
            mock_api = MagicMock()
            mock_api_class.return_value = mock_api

            with patch(
                "custom_components.mitsubishi.config_flow.MitsubishiController"
            ) as mock_controller_class:
                # Create a proper mock that returns the host as unique_id
                mock_controller = MagicMock()
                mock_controller.fetch_status.return_value = True
                # Mock get_status_summary to return a proper dict-like object
                status_summary = {
                    "power": "on",
                    "target_temp": 24.0,
                    "room_temp": 22.5,
                    "mode": "cool",
                    "fan_speed": "auto",
                    "device_info": {
                        "model": "MAC-577IF-2E",
                        "firmware": "1.0.0",
                        "mac_address": "AA:BB:CC:DD:EE:FF"
                    }
                }
                mock_controller.get_status_summary.return_value = status_summary
                mock_controller_class.return_value = mock_controller

                # First create and add an entry successfully
                result = await hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": config_entries.SOURCE_USER}
                )

                result_create = await hass.config_entries.flow.async_configure(
                    result["flow_id"],
                    {"host": "192.168.1.100"},
                )
                assert result_create["type"] == FlowResultType.CREATE_ENTRY

                # Now try to create another entry with the same host
                result2 = await hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": config_entries.SOURCE_USER}
                )

                result2_dup = await hass.config_entries.flow.async_configure(
                    result2["flow_id"],
                    {"host": "192.168.1.100"},
                )

                assert result2_dup["type"] == FlowResultType.ABORT
                assert result2_dup["reason"] == "already_configured"

    @pytest.mark.asyncio
    async def test_form_with_options(self, hass: HomeAssistant, mock_api, mock_controller) -> None:
        """Test configuration with additional options."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.mitsubishi.config_flow.MitsubishiAPI"
        ) as mock_api_class:
            mock_api_class.return_value = mock_api

            with patch(
                "custom_components.mitsubishi.config_flow.MitsubishiController"
            ) as mock_controller_class:
                mock_controller_class.return_value = mock_controller

                result2 = await hass.config_entries.flow.async_configure(
                    result["flow_id"],
                    {
                        "host": "192.168.1.100",
                        "admin_username": "custom_admin",
                        "admin_password": "custom_password",
                        "scan_interval": 60,
                    },
                )

                assert result2["type"] == FlowResultType.CREATE_ENTRY
                assert result2["data"]["admin_username"] == "custom_admin"
                assert result2["data"]["admin_password"] == "custom_password"
                assert result2["data"]["scan_interval"] == 60

    @pytest.mark.asyncio
    async def test_form_unknown_exception(self, hass: HomeAssistant) -> None:
        """Test we handle unknown exceptions."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Simulate exception in validate_input that's not CannotConnect or AbortFlow
        with patch(
            "custom_components.mitsubishi.config_flow.validate_input"
        ) as mock_validate:
            mock_validate.side_effect = ValueError("Unexpected error")

            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {"host": "192.168.1.100"},
            )

            assert result2["type"] == FlowResultType.FORM
            assert result2["errors"] == {"base": "unknown"}

    @pytest.mark.asyncio
    async def test_validate_input_exception_during_validation(self, hass: HomeAssistant) -> None:
        """Test validate_input when exception occurs during validation process."""
        from custom_components.mitsubishi.config_flow import CannotConnect, validate_input

        test_data = {
            "host": "192.168.1.100",
            "encryption_key": "test_key",
        }

        with patch("custom_components.mitsubishi.config_flow.MitsubishiAPI") as mock_api_class, \
             patch("custom_components.mitsubishi.config_flow.MitsubishiController") as mock_controller_class:

            # Set up mocks for exception during get_status_summary
            mock_api = MagicMock()
            mock_api.close = MagicMock()
            mock_api_class.return_value = mock_api

            mock_controller = MagicMock()
            mock_controller.fetch_status = MagicMock(return_value=True)
            mock_controller.get_status_summary = MagicMock(side_effect=Exception("Summary error"))
            mock_controller_class.return_value = mock_controller

            with pytest.raises(CannotConnect):
                await validate_input(hass, test_data)

            # Verify API was closed even when exception occurs
            mock_api.close.assert_called_once()

