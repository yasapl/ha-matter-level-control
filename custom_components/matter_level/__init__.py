"""Matter Level Control integration."""

from __future__ import annotations

import voluptuous as vol
from chip.clusters import Objects as clusters

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.matter.entity import MatterEntity
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_component import DATA_INSTANCES
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_DIRECTION,
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
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_DIRECTION): vol.In((DIRECTION_UP, DIRECTION_DOWN)),
        vol.Optional(ATTR_RATE, default=DEFAULT_RATE): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=254)
        ),
    }
)

STOP_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids})


def _get_matter_light(hass: HomeAssistant, entity_id: str) -> MatterEntity:
    """Return the live Matter entity behind a Home Assistant light entity."""
    light_component = hass.data.get(DATA_INSTANCES, {}).get(LIGHT_DOMAIN)
    if light_component is None:
        raise ServiceValidationError("The Home Assistant light platform is not loaded")

    entity = light_component.get_entity(entity_id)
    if entity is None:
        raise ServiceValidationError(f"Light entity {entity_id} was not found")
    if not isinstance(entity, MatterEntity):
        raise ServiceValidationError(f"Light entity {entity_id} is not a Matter entity")
    if entity._endpoint.get_cluster(clusters.LevelControl) is None:
        raise ServiceValidationError(
            f"Matter light {entity_id} does not expose the Level Control cluster"
        )

    return entity


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Matter Level Control services."""

    async def async_move(call: ServiceCall) -> None:
        """Start continuous native Matter level movement."""
        move_mode = (
            clusters.LevelControl.Enums.MoveModeEnum.kUp
            if call.data[ATTR_DIRECTION] == DIRECTION_UP
            else clusters.LevelControl.Enums.MoveModeEnum.kDown
        )

        for entity_id in call.data[ATTR_ENTITY_ID]:
            entity = _get_matter_light(hass, entity_id)
            await entity.send_device_command(
                clusters.LevelControl.Commands.Move(
                    moveMode=move_mode,
                    rate=call.data[ATTR_RATE],
                    optionsMask=0,
                    optionsOverride=0,
                )
            )

    async def async_stop(call: ServiceCall) -> None:
        """Stop native Matter level movement."""
        for entity_id in call.data[ATTR_ENTITY_ID]:
            entity = _get_matter_light(hass, entity_id)
            await entity.send_device_command(
                clusters.LevelControl.Commands.Stop(
                    optionsMask=0,
                    optionsOverride=0,
                )
            )

    hass.services.async_register(DOMAIN, SERVICE_MOVE, async_move, schema=MOVE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, async_stop, schema=STOP_SCHEMA)

    return True
