"""Matter Level Control integration."""

from __future__ import annotations

import voluptuous as vol
from chip.clusters import Objects as clusters

from homeassistant.components.matter.helpers import get_matter
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_DIRECTION,
    ATTR_ENDPOINT_ID,
    ATTR_NODE_ID,
    ATTR_RATE,
    DEFAULT_RATE,
    DIRECTION_DOWN,
    DIRECTION_UP,
    DOMAIN,
    SERVICE_MOVE,
    SERVICE_STOP,
)

MOVE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NODE_ID): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Required(ATTR_ENDPOINT_ID): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=65535)
        ),
        vol.Required(ATTR_DIRECTION): vol.In((DIRECTION_UP, DIRECTION_DOWN)),
        vol.Optional(ATTR_RATE, default=DEFAULT_RATE): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=254)
        ),
    }
)

STOP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NODE_ID): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Required(ATTR_ENDPOINT_ID): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=65535)
        ),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Matter Level Control services."""

    async def async_move(call: ServiceCall) -> None:
        """Start continuous native Matter level movement."""
        matter = get_matter(hass)
        move_mode = (
            clusters.LevelControl.Enums.MoveModeEnum.kUp
            if call.data[ATTR_DIRECTION] == DIRECTION_UP
            else clusters.LevelControl.Enums.MoveModeEnum.kDown
        )

        await matter.matter_client.send_device_command(
            node_id=call.data[ATTR_NODE_ID],
            endpoint_id=call.data[ATTR_ENDPOINT_ID],
            command=clusters.LevelControl.Commands.Move(
                moveMode=move_mode,
                rate=call.data[ATTR_RATE],
                optionsMask=0,
                optionsOverride=0,
            ),
        )

    async def async_stop(call: ServiceCall) -> None:
        """Stop native Matter level movement."""
        matter = get_matter(hass)

        await matter.matter_client.send_device_command(
            node_id=call.data[ATTR_NODE_ID],
            endpoint_id=call.data[ATTR_ENDPOINT_ID],
            command=clusters.LevelControl.Commands.Stop(
                optionsMask=0,
                optionsOverride=0,
            ),
        )

    hass.services.async_register(DOMAIN, SERVICE_MOVE, async_move, schema=MOVE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, async_stop, schema=STOP_SCHEMA)

    return True
