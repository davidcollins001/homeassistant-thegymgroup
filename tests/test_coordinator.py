import os
import sys
path = os.path.abspath(os.path.join(os.path.abspath(__file__),
                                    '../../custom_components'))
sys.path.insert(0, path)
# import pytest
import datetime as dt
from unittest.mock import MagicMock

from thegymgroup.coordinator import TheGymGroupCoordinator


def do_assert(v1, v2):
    assert v1 == v2, f"{v1} does not match {v2}"


# @pytest.fixture
def coordinator():
    hass = MagicMock()
    entry = MagicMock()
    return TheGymGroupCoordinator(hass, entry)


def build_gym_data():
    return {'gymLocationId': 'ee578789-b83a-489f-8044-187e67a11dfc',
            'gymLocationName': 'London Leyton',
            'currentCapacity': 105,
            'currentPercentage': 44,
            'historical': [{'hour': '12AM', 'percentage': 27},
                           {'hour': '2AM', 'percentage': 4},
                           {'hour': '4AM', 'percentage': 10},
                           {'hour': '6AM', 'percentage': 26},
                           {'hour': '8AM', 'percentage': 27},
                           {'hour': '10AM', 'percentage': 30},
                           {'hour': '12PM', 'percentage': 29},
                           {'hour': '2PM', 'percentage': 28},
                           {'hour': '4PM', 'percentage': 35},
                           {'hour': '6PM', 'percentage': 44},
                           {'hour': '8PM', 'percentage': 68},
                           {'hour': '10PM', 'percentage': 88}],
            'status': 'open'}


def test_build_visit_data(coordinator):
    gym_data = build_gym_data()

    visits_data = [
        # no visits to gym yet today
        ({'checkIns': []},
         (2025, 4, 3, 7, 5, 0), (1970, 1, 1, 0, 0, 0), "off", None, {},
        ),

        # at gym
        ({'checkIns': [{'gymLocationName': 'London Leyton',
                        'gymLocationAddress': 'Marshall Road',
                        'checkInDate': '2025-04-03T07:00:00',
                        'timezone': 'Europe/London',
                        'duration': 0}]},
         (2025, 4, 3, 7, 15, 0), (2025, 4, 3, 7, 15, 0), "on", 0, {},
        ),

        # at gym
        ({'checkIns': [{'gymLocationName': 'London Leyton',
                        'gymLocationAddress': 'Marshall Road',
                        'checkInDate': '2025-04-03T07:00:00',
                        'timezone': 'Europe/London',
                        'duration': 0}]},
         (2025, 4, 3, 7, 25, 0), (2025, 4, 3, 7, 15, 0), "on", 0, {},
        ),

        # left gym
        ({'checkIns': [{'gymLocationName': 'London Leyton',
                        'gymLocationAddress': 'Marshall Road',
                        'checkInDate': '2025-04-03T07:00:00',
                        'timezone': 'Europe/London',
                        'duration': 4500000}]},
         (2025, 4, 3, 7, 35, 0), (2025, 4, 3, 7, 35, 0), "off", 75, {(2025, 14): 75.0},
        ),

        # later, not at gym
        ({'checkIns': [{'gymLocationName': 'London Leyton',
                        'gymLocationAddress': 'Marshall Road',
                        'checkInDate': '2025-04-03T07:00:00',
                        'timezone': 'Europe/London',
                        'duration': 4500000}]},
         (2025, 4, 3, 7, 45, 0), (2025, 4, 3, 7, 35, 0), "off", 75, {(2025, 14): 75.0},
        ),
    ]

    for (visits, exp_sync, exp_updated, exp_presence, exp_duration,
         exp_weekly) in visits_data:
        sync_dt = dt.datetime(*exp_sync)
        data = coordinator.build_visit_data(sync_dt, gym_data, visits)
        # copy data to Coordinator like base class would
        coordinator.data = data

        do_assert(dt.datetime(*exp_sync), coordinator.last_sync)
        do_assert(dt.datetime(*exp_updated), coordinator.last_updated)
        do_assert(exp_presence, data['gymPresence'])

        check_ins = data.get('checkIns')
        if exp_duration is None:
            do_assert(check_ins, [])
        else:
            do_assert( check_ins[-1]['duration'], exp_duration)

        do_assert(exp_weekly, data['weeklyTotal'])


if __name__ == "__main__":
    obj = coordinator()
    test_build_visit_data(obj)
