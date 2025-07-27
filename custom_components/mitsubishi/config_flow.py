"""Config flow for Mitsubishi Air Conditioner integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from pymitsubishi import MitsubishiAPI, MitsubishiController

from .const import DOMAIN, CONF_ENABLE_CAPABILITY_DETECTION

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_ENABLE_CAPABILITY_DETECTION, default=True): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    api = MitsubishiAPI(device_ip=data[CONF_HOST])
    controller = MitsubishiController(api=api)
    
    try:
        # Test connection
        success = await hass.async_add_executor_job(controller.fetch_status)
        if not success:
            raise CannotConnect
        
        # Get device info for unique_id
        summary = controller.get_status_summary()
        await hass.async_add_executor_job(api.close)
        
        return {
            "title": f"Mitsubishi AC ({summary.get('mac', data[CONF_HOST])})",
            "unique_id": summary.get('mac') or summary.get('serial') or data[CONF_HOST]
        }
        
    except Exception:
        await hass.async_add_executor_job(api.close)
        raise CannotConnect


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mitsubishi Air Conditioner."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(info["unique_id"]) 
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
