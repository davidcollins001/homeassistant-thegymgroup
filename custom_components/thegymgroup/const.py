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
from homeassistant.components.binary_sensor import (
    BinarySensorEntityDescription,
    BinarySensorDeviceClass
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)

DOMAIN = "thegymgroup"
DATA_COORDINATOR = "coordinator"
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=15)
EVENT_RESET = "reset"


@dataclass(kw_only=True)
class GymGroupEntityDescription(SensorEntityDescription):
    """Describes sensor entity"""
    path: str


@dataclass(kw_only=True)
class GymGroupBinaryEntityDescription(BinarySensorEntityDescription):
    """Describes sensor entity"""
    path: str


ACCOUNT_ENTITIES = (
    GymGroupEntityDescription(key="chain_name",
                              translation_key="chain_name",
                              path="profile/chainName",
                              icon="mdi:bank-outline"),
    GymGroupEntityDescription(key="home_gym",
                              translation_key="home_gym",
                              path="profile/homeClubName",
                              icon="mdi:home"),
    GymGroupEntityDescription(key="account_status",
                              translation_key="account_status",
                              path="profile/customInfo.accountStatus",
                              icon="mdi:account-alert"),
    GymGroupEntityDescription(key="membership_type",
                              translation_key="membership_type",
                              path="profile/membershipType",
                              icon = "mdi:wallet-membership"),
)

GYM_ENTITIES = (
    GymGroupEntityDescription(key="occupancy",
                              translation_key="occupancy",
                              path="data/currentCapacity",
                              icon="mdi:human-queue",
                              state_class=SensorStateClass.TOTAL),
)

GYM_STATUS_ENTITIES = (
    GymGroupBinaryEntityDescription(key="gym_status",
                                    translation_key="gym_status",
                                    path="data/status",
                                    icon="mdi:store-clock",
                                    device_class=BinarySensorDeviceClass.DOOR),
    GymGroupBinaryEntityDescription(key="gym_presence",
                                    translation_key="gym_presence",
                                    path="data/gymPresence",
                                    icon="mdi:weight-lifter",
                                    device_class=BinarySensorDeviceClass.OCCUPANCY),
)

WORKOUT_ENTITIES = (
    GymGroupEntityDescription(key="last_workout_duration",
                              translation_key="last_workout_duration",
                              path="data/checkIns.duration",
                              unit_of_measurement=UnitOfTime.MINUTES,
                              icon="mdi:weight-lifter",
                              state_class=SensorStateClass.MEASUREMENT,
                              # device_class=SensorDeviceClass.DURATION,
                             ),

    GymGroupEntityDescription(key="workout_duration_this_week",
                              translation_key="workout_duration_this_week",
                              path="weeklyTotal",
                              unit_of_measurement=UnitOfTime.MINUTES,
                              icon="mdi:weight-lifter",
                              state_class=SensorStateClass.MEASUREMENT,
                              # device_class=SensorDeviceClass.DURATION),
                             ),

    GymGroupEntityDescription(key="workout_duration_this_month",
                              translation_key="workout_duration_this_month",
                              path="monthlyTotal",
                              unit_of_measurement=UnitOfTime.MINUTES,
                              icon="mdi:weight-lifter",
                              state_class=SensorStateClass.MEASUREMENT,
                              # device_class=SensorDeviceClass.DURATION),
                             ),

    GymGroupEntityDescription(key="workout_duration_this_year",
                              translation_key="workout_duration_this_year",
                              path="yearlyTotal",
                              unit_of_measurement=UnitOfTime.MINUTES,
                              icon="mdi:weight-lifter",
                              state_class=SensorStateClass.MEASUREMENT,
                             ),

    GymGroupEntityDescription(key="workout_visits_this_month",
                              translation_key="workout_visits_this_month",
                              path="monthlyVisitCount",
                              icon="mdi:weight-lifter",
                              state_class=SensorStateClass.MEASUREMENT,
                             ),

    GymGroupEntityDescription(key="workout_visits_this_year",
                              translation_key="workout_visits_this_year",
                              path="yearlyVisitCount",
                              icon="mdi:weight-lifter",
                              state_class=SensorStateClass.MEASUREMENT,
                             ),
)
