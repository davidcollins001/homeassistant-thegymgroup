"""Platform for The Gym Group integration."""
import logging
import datetime as dt

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity, DataUpdateCoordinator,
)

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    ACCOUNT_ENTITIES,
    WORKOUT_ENTITIES,
    GYM_ENTITIES,
    EVENT_RESET,
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
            "location": self.coordinator.data["gymLocationName"],
        })

        return attributes


class GymGroupVisitSensor(GymGroupMemberSensor):
    async def async_added_to_hass(self):
        """Complete the initialization."""
        await super().async_added_to_hass()
        # register this sensor in the coordinator
        # self.coordinator.register_entity(self.name, self.entity_id)

        event_to_listen = f"{self.coordinator.name}_{EVENT_RESET}"
        self.hass.bus.async_listen(event_to_listen,
                                   lambda event: self._handle_reset(event))

    @callback
    def _handle_reset(self, event: Event):
        # write the updated state
        self.hass.add_job(self.async_write_ha_state)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        check_ins =  self.coordinator.data.get("checkIns")

        from homeassistant.components.sensor import SensorStateClass
        if self.entity_description.state_class == SensorStateClass.TOTAL:
            self._attr_last_reset = dt.datetime.combine(dt.date.today(),
                                                        dt.time.min)

        if check_ins:
            return check_ins[0]["duration"]
        return 0

    @property
    def extra_state_attributes(self):
        """Sensor attributes"""
        if not self.coordinator.data:
            return {}

        attributes = super().extra_state_attributes
        check_ins =  self.coordinator.data.get("checkIns")
        if check_ins:
            attributes.update({
                "check_in": check_ins[0]["checkInDate"],
                "location": check_ins[0]["gymLocationName"],
            })

        return attributes

    # @property
    # def available(self):
        # return (super().available and "checkIns" in self.coordinator.data)

    @property
    def native_unit_of_measurement(self):
        return self.entity_description.unit_of_measurement
