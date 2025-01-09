"""Constants for the The Gym Group integration."""
from datetime import timedelta
from typing import NamedTuple
from dataclasses import dataclass

from homeassistant.const import (
    UnitOfMass,
    UnitOfTime,
    UnitOfLength,
    PERCENTAGE,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)

DOMAIN = "thegymgroup"
DATA_COORDINATOR = "coordinator"
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=15)


@dataclass(kw_only=True)
class GymGroupEntityDescription(SensorEntityDescription):
    """Describes sensor entity"""
    path: str


ACCOUNT_ENTITY_LIST = (
    GymGroupEntityDescription(key="chain_name",
                              translation_key="chain_name",
                              path="profile/chainName",
                              icon="mdi:bank-outline"),
    GymGroupEntityDescription(key="home_gym",
                              translation_key="home_gym",
                              path="profile/homeClubName",
                              icon="mdi:home"),
    GymGroupEntityDescription(key="occupancy",
                              translation_key="occupancy",
                              path="data/currentCapacity",
                              icon="mdi:human-queue",
                              state_class=SensorStateClass.TOTAL),
    GymGroupEntityDescription(key="account_status",
                              translation_key="account_status",
                              path="profile/customInfo.accountStatus",
                              icon="mdi:account-alert"),
    GymGroupEntityDescription(key="gym_status",
                              translation_key="gym_status",
                              path="data/status",
                              icon="mdi:store-clock"),
    GymGroupEntityDescription(key="membership_type",
                              translation_key="membership_type",
                              path="profile/membershipType",
                              icon = "mdi:wallet-membership"),
)

WORKOUT_ENTITY_LIST = (
    GymGroupEntityDescription(key="last_workout_duration",
                              translation_key="last_workout_duration",
                              path="data/checkIn.duration",
                              unit_of_measurement=UnitOfTime.MILLISECONDS,
                              icon="mdi:weight-lifter",
                              device_class=SensorDeviceClass.DURATION),
    # "data/checkIn.checkInDate": ["Last Check-in", None, "mdi:weight-lifter", None, None, True],
    # "data/checkIn.gymLocationName": ["Last Workout Location", None, "mdi:weight-lifter", None, None, True],
)
