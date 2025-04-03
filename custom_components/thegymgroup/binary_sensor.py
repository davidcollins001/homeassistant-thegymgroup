"""Platform for The Gym Group integration."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity, DataUpdateCoordinator,
)

from .const import DATA_COORDINATOR, DOMAIN, GYM_STATUS_ENTITIES
from .entity import GymGroupBaseEntity

_LOGGER = logging.getLogger(__name__)

ON_STATES = ["open", "active", "on"]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up The Gym Group sensor based on a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    unique_id = entry.data[CONF_ID].split('@')[0]

    entities = []
    for descr in GYM_STATUS_ENTITIES:
        _LOGGER.debug("Registering entity: %s", descr)
        entities.append(GymGroupStatusSensor(unique_id, coordinator, descr))

    async_add_entities(entities, update_before_add=True)

    return True


class GymGroupStatusSensor(GymGroupBaseEntity, BinarySensorEntity):
    @property
    def is_on(self):
        data = self.get_value(self.entity_description.path)
        return data.lower() in ON_STATES
