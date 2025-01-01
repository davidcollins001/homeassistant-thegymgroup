"""Config flow for The Gym Group integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_ID, CONF_PASSWORD, CONF_USERNAME, CONF_SCAN_INTERVAL
)

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        # vol.Required(CONF_SCAN_INTERVAL,
                     # default=DEFAULT_UPDATE_INTERVAL):
    }
)


class TheGymGroupConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for The Gym Group."""

    VERSION = 1

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors or {},
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return await self._show_setup_form()

        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        unique_id = username  # .split('@')[0]

        # TODO: login to check credentials

        await self.async_set_unique_id(username)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=username,
            data={
                CONF_ID: unique_id,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
            },
        )
