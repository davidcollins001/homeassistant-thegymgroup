from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class GymGroupBaseEntity(CoordinatorEntity):
    def __init__(self, unique_id, coordinator, description):
        super().__init__(coordinator)

        self._unique_id = unique_id
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.name}_{description.translation_key}"
        self._attr_has_entity_name = True

    def get_value(self, path):
        """Return the state of the sensor."""
        field, locs = path.split('/')
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
