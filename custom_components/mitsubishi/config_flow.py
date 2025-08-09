"""Config flow for Mitsubishi Air Conditioner integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.exceptions import HomeAssistantError
from pymitsubishi import MitsubishiAPI, MitsubishiController

from .const import (
    CONF_ADMIN_PASSWORD,
    CONF_ADMIN_USERNAME,
    CONF_ENABLE_CAPABILITY_DETECTION,
    CONF_ENCRYPTION_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ENCRYPTION_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_ENCRYPTION_KEY, default=DEFAULT_ENCRYPTION_KEY): str,
        vol.Optional(CONF_ADMIN_USERNAME, default=DEFAULT_ADMIN_USERNAME): str,
        vol.Optional(CONF_ADMIN_PASSWORD, default=DEFAULT_ADMIN_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=300)
        ),
        vol.Optional(CONF_ENABLE_CAPABILITY_DETECTION, default=True): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    _LOGGER.debug("Starting validation for host: %s", data[CONF_HOST])

    encryption_key = data.get(CONF_ENCRYPTION_KEY, DEFAULT_ENCRYPTION_KEY)
    _LOGGER.debug("Using encryption key: %s", encryption_key)

    api = MitsubishiAPI(device_ip=data[CONF_HOST], encryption_key=encryption_key)
    controller = MitsubishiController(api=api)

    try:
        # Test connection
        _LOGGER.debug("Attempting to fetch status from device")
        success = await hass.async_add_executor_job(controller.fetch_status)
        _LOGGER.debug("Fetch status result: %s", success)
        if not success:
            _LOGGER.error("Failed to fetch status from device")
            raise CannotConnect

        # Get device info for unique_id
        _LOGGER.debug("Getting status summary")
        summary = controller.get_status_summary()
        _LOGGER.debug("Status summary: %s", summary)
        await hass.async_add_executor_job(api.close)

        return {
            "title": f"Mitsubishi AC ({summary.get('mac', data[CONF_HOST])})",
            "unique_id": summary.get("mac") or summary.get("serial") or data[CONF_HOST],
        }

    except Exception as e:
        _LOGGER.error("Exception during validation: %s", str(e), exc_info=True)
        await hass.async_add_executor_job(api.close)
        raise CannotConnect from e


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mitsubishi Air Conditioner."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        """Handle the initial step."""
        _LOGGER.debug("Config flow async_step_user called with input: %s", user_input)
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("Processing user input for config flow")
            try:
                _LOGGER.debug("Calling validate_input")
                info = await validate_input(self.hass, user_input)
                _LOGGER.debug("Validation successful, info: %s", info)

                # Check if already configured
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()

                _LOGGER.debug("Creating config entry")
                return self.async_create_entry(title=info["title"], data=user_input)

            except CannotConnect:
                _LOGGER.error("Cannot connect to device")
                errors["base"] = "cannot_connect"
            except AbortFlow:
                # Re-raise AbortFlow to allow proper flow termination
                raise
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        else:
            _LOGGER.debug("No user input provided, showing form")

        _LOGGER.debug("Showing config form with errors: %s", errors)
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the Mitsubishi integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("Processing options user input: %s", user_input)
            try:
                # Validate the new configuration
                _LOGGER.debug("Validating new configuration")
                await validate_input(self.hass, user_input)
                _LOGGER.debug("Validation successful for options")

                # Update the config entry with new data
                self.hass.config_entries.async_update_entry(self._config_entry, data=user_input)

                # Trigger reload of the integration to apply changes
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)

                return self.async_create_entry(title="", data={})

            except CannotConnect:
                _LOGGER.error("Cannot connect to device with new settings")
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in options flow")
                errors["base"] = "unknown"

        # Create options schema with current values as defaults
        current_host = self._config_entry.data.get(CONF_HOST, "")
        current_encryption_key = self._config_entry.data.get(
            CONF_ENCRYPTION_KEY, DEFAULT_ENCRYPTION_KEY
        )
        current_admin_username = self._config_entry.data.get(
            CONF_ADMIN_USERNAME, DEFAULT_ADMIN_USERNAME
        )
        current_admin_password = self._config_entry.data.get(
            CONF_ADMIN_PASSWORD, DEFAULT_ADMIN_PASSWORD
        )
        current_scan_interval = self._config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_capability_detection = self._config_entry.data.get(
            CONF_ENABLE_CAPABILITY_DETECTION, True
        )

        options_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Optional(CONF_ENCRYPTION_KEY, default=current_encryption_key): str,
                vol.Optional(CONF_ADMIN_USERNAME, default=current_admin_username): str,
                vol.Optional(CONF_ADMIN_PASSWORD, default=current_admin_password): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_scan_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=300)
                ),
                vol.Optional(
                    CONF_ENABLE_CAPABILITY_DETECTION,
                    default=current_capability_detection,
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema, errors=errors)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
