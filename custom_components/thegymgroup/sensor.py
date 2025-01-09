"""Platform for The Gym Group integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity, DataUpdateCoordinator,
)

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    ACCOUNT_ENTITY_LIST,
    WORKOUT_ENTITY_LIST,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up The Gym Group sensor based on a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    unique_id = entry.data[CONF_ID].split('@')[0]

    entities = []
    for descr in ACCOUNT_ENTITY_LIST:
        _LOGGER.debug("Registering entity: %s", descr)
        entities.append(GymGroupMemberSensor(unique_id, coordinator, descr))

    for descr in WORKOUT_ENTITY_LIST:
        _LOGGER.debug("Registering entity: %s", descr)
        entities.append(GymGroupVisitSensor(unique_id, coordinator, descr))

    async_add_entities(entities, update_before_add=True)

    return True


class GymGroupMemberSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, unique_id, coordinator, description):
        super().__init__(coordinator)

        self._unique_id = unique_id
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.name}_{description.key}"
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the state of the sensor."""
        field, locs = self.entity_description.path.split('/')
        locs = locs.split('.')

        data = getattr(self.coordinator, field)
        for loc in locs:
            if data:
                data = data.get(loc)

        return data

    @property
    def extra_state_attributes(self):
        """Sensor attributes"""
        if not self.coordinator.data:
            return {}

        attributes = {
            "last_synced": self.coordinator.last_sync
        }

        return attributes

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": "The Gym Group",
            "manufacturer": "The Gym Group",
        }

    @property
    def entity_registry_enabled_default(self):
        """if entity should be enabled when first added to the entity registry"""
        # return self._enabled_default
        return True

    @property
    def available(self):
        return super().available and self.coordinator.data


class GymGroupVisitSensor(GymGroupMemberSensor):
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data["checkIns"][0]["duration"]

    @property
    def extra_state_attributes(self):
        """Sensor attributes"""
        if not self.coordinator.data:
            return {}

        return {
            "check_in": self.coordinator.data["checkIns"][0]["checkInDate"],
            "location": self.coordinator.data["checkIns"][0]["gymLocationName"],
            "last_synced": self.coordinator.last_sync,
        }

    @property
    def available(self):
        return (super().available and self.coordinator.data
                and "checkIns" in self.coordinator.data)

    @property
    def native_unit_of_measurement(self):
        return self.entity_description.unit_of_measurement

