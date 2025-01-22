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
    ACCOUNT_ENTITIES,
    WORKOUT_ENTITIES,
    GYM_ENTITIES,
)
from .entity import GymGroupBaseEntity

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
    for descr in ACCOUNT_ENTITIES:
        _LOGGER.debug("Registering entity: %s", descr)
        entities.append(GymGroupMemberSensor(unique_id, coordinator, descr))

    for descr in GYM_ENTITIES:
        _LOGGER.debug("Registering entity: %s", descr)
        entities.append(GymGroupGymSensor(unique_id, coordinator, descr))

    for descr in WORKOUT_ENTITIES:
        _LOGGER.debug("Registering entity: %s", descr)
        entities.append(GymGroupVisitSensor(unique_id, coordinator, descr))

    async_add_entities(entities, update_before_add=True)

    return True


class GymGroupMemberSensor(GymGroupBaseEntity, SensorEntity):
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.get_value(self.entity_description.path)


class GymGroupGymSensor(GymGroupMemberSensor):
    @property
    def extra_state_attributes(self):
        """Sensor attributes"""
        if not self.coordinator.data:
            return {}

        attributes = super().extra_state_attributes
        attributes.update({
            "location": self.coordinator.data["checkIns"][0]["gymLocationName"],
        })

        return attributes


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

        attributes = super().extra_state_attributes
        attributes.update({
            "check_in": self.coordinator.data["checkIns"][0]["checkInDate"],
            "location": self.coordinator.data["checkIns"][0]["gymLocationName"],
        })

        return attributes

    @property
    def available(self):
        return (super().available and "checkIns" in self.coordinator.data)

    @property
    def native_unit_of_measurement(self):
        return self.entity_description.unit_of_measurement
