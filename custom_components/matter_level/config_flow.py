"""Config flow for Matter Level Control."""

from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class MatterLevelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Matter Level Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the single Matter Level Control config entry."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Matter Level Control", data={})

        return self.async_show_form(step_id="user")
