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
from homeassistant.helpers import selector
from pymitsubishi import MitsubishiAPI, MitsubishiController

from .const import (
    CONF_ADMIN_PASSWORD,
    CONF_ADMIN_USERNAME,
    CONF_ENCRYPTION_KEY,
    CONF_EXPERIMENTAL_FEATURES,
    CONF_EXTERNAL_TEMP_ENTITY,
    CONF_REMOTE_TEMP_MODE,
    CONF_SCAN_INTERVAL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ENCRYPTION_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def _get_experimental_schema(suggested_value: str | None = None) -> vol.Schema:
    """Get the schema for experimental features configuration."""
    entity_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["sensor", "input_number", "number"],
        )
    )
    if suggested_value:
        return vol.Schema(
            {
                vol.Optional(
                    CONF_EXTERNAL_TEMP_ENTITY,
                    description={"suggested_value": suggested_value},
                ): entity_selector,
            }
        )
    return vol.Schema(
        {
            vol.Optional(CONF_EXTERNAL_TEMP_ENTITY): entity_selector,
        }
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
        vol.Optional(CONF_EXPERIMENTAL_FEATURES, default=False): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    _LOGGER.debug("Starting validation for host: %s", data[CONF_HOST])

    encryption_key = data.get(CONF_ENCRYPTION_KEY, DEFAULT_ENCRYPTION_KEY)
    _LOGGER.debug("Using encryption key: %s", encryption_key)

    api = MitsubishiAPI(device_host_port=data[CONF_HOST], encryption_key=encryption_key)
    controller = MitsubishiController(api=api)

    try:
        # Test connection
        _LOGGER.debug("Attempting to fetch status from device")
        try:
            state = await hass.async_add_executor_job(controller.fetch_status)
        except Exception as e:
            _LOGGER.error("Failed to fetch status from device")
            raise CannotConnect from e

        # Get device info for unique_id
        _LOGGER.debug("Status: %s", state)
        await hass.async_add_executor_job(api.close)

        return {
            "title": f"Mitsubishi AC ({state.mac or data[CONF_HOST]})",
            "unique_id": state.mac or state.serial or data[CONF_HOST],
        }

    except Exception as e:
        _LOGGER.error("Exception during validation: %s", str(e), exc_info=True)
        await hass.async_add_executor_job(api.close)
        raise CannotConnect from e


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mitsubishi Air Conditioner."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._connection_data: dict[str, Any] = {}
        self._experimental_features: bool = False
        self._device_info: dict[str, Any] = {}

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
                # Extract experimental features flag
                self._experimental_features = user_input.pop(CONF_EXPERIMENTAL_FEATURES, False)

                _LOGGER.debug("Calling validate_input")
                info = await validate_input(self.hass, user_input)
                _LOGGER.debug("Validation successful, info: %s", info)

                # Check if already configured
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()

                # Store for later
                self._connection_data = user_input
                self._device_info = info

                # If experimental features enabled, go to step 2
                if self._experimental_features:
                    return await self.async_step_experimental()

                # Otherwise, create entry directly
                return self._create_entry(external_temp_entity=None)

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

    async def async_step_experimental(self, user_input: dict[str, Any] | None = None) -> Any:
        """Step 2: Configure experimental features (external temperature sensor)."""
        if user_input is not None:
            external_temp_entity = user_input.get(CONF_EXTERNAL_TEMP_ENTITY)
            return self._create_entry(external_temp_entity=external_temp_entity)

        return self.async_show_form(step_id="experimental", data_schema=_get_experimental_schema())

    def _create_entry(self, external_temp_entity: str | None) -> Any:
        """Create the config entry with options."""
        _LOGGER.debug("Creating config entry")

        # Build options
        options: dict[str, Any] = {
            CONF_EXPERIMENTAL_FEATURES: self._experimental_features,
        }
        if self._experimental_features and external_temp_entity:
            options[CONF_EXTERNAL_TEMP_ENTITY] = external_temp_entity

        return self.async_create_entry(
            title=self._device_info["title"],
            data=self._connection_data,
            options=options,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the Mitsubishi integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry
        self._connection_data: dict[str, Any] = {}
        self._experimental_features: bool = False

    @property
    def config_entry(self) -> config_entries.ConfigEntry:
        """Return the config entry."""
        return self._config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        """Step 1: Connection settings and experimental features toggle."""
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("Processing options step init: %s", user_input)
            try:
                # Extract experimental features flag
                self._experimental_features = user_input.pop(CONF_EXPERIMENTAL_FEATURES, False)

                # Validate the connection configuration
                _LOGGER.debug("Validating new configuration")
                await validate_input(self.hass, user_input)
                _LOGGER.debug("Validation successful for options")

                # Store connection data for later
                self._connection_data = user_input

                # If experimental features enabled, go to step 2 for entity selection
                if self._experimental_features:
                    return await self.async_step_experimental()

                # Otherwise, save and finish
                return await self._async_save_options(external_temp_entity=None)

            except CannotConnect:
                _LOGGER.error("Cannot connect to device with new settings")
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in options flow")
                errors["base"] = "unknown"

        # Create options schema with current values as defaults
        current_host = self.config_entry.data.get(CONF_HOST, "")
        current_encryption_key = self.config_entry.data.get(
            CONF_ENCRYPTION_KEY, DEFAULT_ENCRYPTION_KEY
        )
        current_admin_username = self.config_entry.data.get(
            CONF_ADMIN_USERNAME, DEFAULT_ADMIN_USERNAME
        )
        current_admin_password = self.config_entry.data.get(
            CONF_ADMIN_PASSWORD, DEFAULT_ADMIN_PASSWORD
        )
        current_scan_interval = self.config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_experimental = self.config_entry.options.get(CONF_EXPERIMENTAL_FEATURES, False)

        options_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Optional(CONF_ENCRYPTION_KEY, default=current_encryption_key): str,
                vol.Optional(CONF_ADMIN_USERNAME, default=current_admin_username): str,
                vol.Optional(CONF_ADMIN_PASSWORD, default=current_admin_password): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_scan_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=300)
                ),
                vol.Optional(CONF_EXPERIMENTAL_FEATURES, default=current_experimental): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema, errors=errors)

    async def async_step_experimental(self, user_input: dict[str, Any] | None = None) -> Any:
        """Step 2: Configure experimental features (external temperature sensor)."""
        if user_input is not None:
            external_temp_entity = user_input.get(CONF_EXTERNAL_TEMP_ENTITY)
            return await self._async_save_options(external_temp_entity=external_temp_entity)

        current_external_temp_entity = self.config_entry.options.get(CONF_EXTERNAL_TEMP_ENTITY, "")

        return self.async_show_form(
            step_id="experimental",
            data_schema=_get_experimental_schema(current_external_temp_entity or None),
        )

    async def _async_save_options(self, external_temp_entity: str | None) -> Any:
        """Save connection data and options."""
        # Update the config entry data (connection settings)
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=self._connection_data,
        )

        # Trigger reload of the integration to apply changes
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)

        # Build new options
        new_options: dict[str, Any] = {
            CONF_EXPERIMENTAL_FEATURES: self._experimental_features,
        }
        if self._experimental_features:
            # Only preserve experimental settings when experimental features are enabled
            if external_temp_entity:
                new_options[CONF_EXTERNAL_TEMP_ENTITY] = external_temp_entity
            # Preserve remote_temp_mode from existing options
            if CONF_REMOTE_TEMP_MODE in self.config_entry.options:
                new_options[CONF_REMOTE_TEMP_MODE] = self.config_entry.options[
                    CONF_REMOTE_TEMP_MODE
                ]
        # When experimental features are disabled, don't preserve remote_temp_mode
        # This ensures a clean state when the feature is turned off

        return self.async_create_entry(title="", data=new_options)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
