import time
import aiohttp
import asyncio
import logging
import operator as op
import datetime as dt

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL, EVENT_RESET

_LOGGER = logging.getLogger(__name__)


def dt2str(ts):
    # return ts.isoformat(sep="T", timespec="seconds")
    return ts.strftime("%Y-%m-%dT%H:%M:%S")


def set_dt(c):
    # add 1 hour for daylight savings
    c['checkInDate'] = dt.datetime.fromisoformat(c['checkInDate']) \
        + dt.timedelta(hours=time.localtime().tm_isdst)
    c['duration'] = c['duration'] / 1000 / 60
    return c


class TheGymGroupCoordinator(DataUpdateCoordinator):
    """Coordinator is responsible for querying the device at a specified route."""

    def __init__(self, hass: HomeAssistant, entry,
                 poll_interval=DEFAULT_UPDATE_INTERVAL):
        """Initialise a custom coordinator."""
        self.entry = entry
        self.last_sync = dt.datetime(1970, 1, 1)
        self.last_updated = dt.datetime(1970, 1, 1)
        self.last_check_in = dt.datetime(1970, 1, 1)

        super().__init__(hass, _LOGGER, name=DOMAIN,
                         update_interval=poll_interval,
                         update_method=self.async_refresh_data)
        self.data = {}

        self.base_url = "https://thegymgroup.netpulse.com/np"
        self.headers = {
            "accept": "application/json",
            "accept-encoding": "gzip",
            "connection": "Keep-Alive",
            "host": "thegymgroup.netpulse.com",
            "user-agent": "okhttp/3.12.3",
            "x-np-api-version": "1.5",
            "x-np-user-agent": ("clientType=MOBILE_DEVICE; devicePlatform=ANDROID; "
                                "deviceUid=; "
                                "applicationName=The Gym Group; "
                                "applicationVersion=5.0; "
                                "applicationVersionCode=38"),
        }

        # async_track_time_change(hass, self._async_reset, hour=23, minute=58, second=0)

    async def async_login(self, attempt=0):
        headers = {**self.headers,
                   "content-length": "56",
                   "content-type": "application/x-www-form-urlencoded"}

        creds = {"username": self.entry.data[CONF_USERNAME],
                 "password": self.entry.data[CONF_PASSWORD]}

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/exerciser/login",
                                    data=creds) as resp:
                if resp.status == 401:
                    msg = f"Login failure: {resp.text}"
                    _LOGGER.error(msg)
                    raise ConfigEntryAuthFailed(msg)

                try:
                    cookie = resp.headers.get("Set-Cookie")
                    data = await resp.json()
                except Exception as e:
                    _LOGGER.critical(f"login failed: {resp.status} {e}")
                    await asyncio.sleep(attempt)
                    await self.async_login(2 ** attempt)

        self.headers["cookie"] = cookie
        self.profile = data

        return True

    async def _async_reset(self, *args):
        _LOGGER.info("Resetting thegymgroup sensor {}!".format(self.name))
        self.data.pop("checkIns", None)
        self.hass.bus.fire(f"{self.name}_{EVENT_RESET}")

    async def fetch(self, url, session, attempt=0):
        async with session.get(f"{self.base_url}/{url}", headers=self.headers) \
                as response:
            if response.status != 200:
                err = await response.text()
                _LOGGER.error(f"failed for {url}: {response.status}: {err}")
                await asyncio.sleep(attempt)
                await self.async_login()
                return await self.fetch(url, session, 2 ** attempt)

            return await response.json()

    async def async_refresh_data(self):
        """Fetch the data from the device."""
        user_id = self.profile["uuid"]
        gym_id = self.profile["homeClubUuid"]
        url = (f"{self.base_url}/exerciser/{user_id}/"
               f"gym-busyness?gymLocationId={gym_id}")

        async with aiohttp.ClientSession() as session:
            # sync current occupancy
            gym_occupancy = self.fetch(
                f"thegymgroup/v1.0/exerciser/{user_id}/gym-busyness?"
                f"gymLocationId={gym_id}",
                session
            )

            start_date = ''
            if self.last_sync:
                start_date = f"startDate={dt2str(self.last_sync)}"

            # sync gym visits
            gym_visit = self.fetch(
                f"exercisers/{user_id}/check-ins/history?"
                f"{start_date}&endDate={dt2str(dt.datetime.now())}",
                session
            )

            gym_data, visits = await asyncio.gather(gym_occupancy, gym_visit)

        sync_dt = dt.datetime.now(dt.timezone.utc)
        return self.build_visit_data(sync_dt, gym_data, visits)

    def build_visit_data(self, sync_dt, gym_data, visits):
        last_updated = self.last_updated

        # totals = self.data.get("totals", {})
        # week_visits = totals.get("weekly",
                                 # self.data.get("weeklyTotal", {}))
        # month_visits = totals.get("totals",
                                  # self.data.get("monthlyTotal", {}))
        new_check_ins = visits.get("checkIns")
        check_ins = self.data.get("checkIns", [])
        gym_presence = self.data.get("gymPresence", "off")
        week_visits = self.data.get("weeklyTotal", {})
        month_visits = self.data.get("monthlyTotal", {})
        year_visits = self.data.get("yearlyTotal", {})
        month_visit_count = self.data.get("monthlyVisitCount", {})
        year_visit_count = self.data.get("yearlyVisitCount", {})

        # last "check in" is always shown, ignore if it's already been processed
        today = dt.datetime.combine(self.last_sync.date(), dt.time.min)
        # check in will be after sync time
        last_check_in = max(today, self.last_check_in)
        todays_check_ins = sorted(filter(lambda c: c['checkInDate'] > today,
                                         map(set_dt, new_check_ins)),
                                  key=op.itemgetter('checkInDate'),
                                  reverse=False)

        # for check_in in unseen_check_ins:
        for check_in in todays_check_ins:
            # an unseen check in
            if check_in not in check_ins:
                duration = check_in['duration']
                check_in_date = check_in['checkInDate']
                self.last_check_in = check_in_date
                check_ins = check_ins + [check_in]
                last_updated = sync_dt

                if duration > 0:
                    gym_presence = "off"
                    cal = check_in_date.isocalendar()
                    wk_ndx = (cal.year, cal.week)
                    mnth_ndx = (check_in_date.year, check_in_date.month)
                    yr_ndx = check_in_date.year
                    week_visits[wk_ndx] = week_visits.get(wk_ndx, 0) + duration
                    month_visits[mnth_ndx] = month_visits.get(mnth_ndx, 0) + duration
                    year_visits[yr_ndx] = year_visits.get(yr_ndx, 0) + duration
                    month_visit_count[mnth_ndx] = month_visit_count.get(mnth_ndx, 0) + 1
                    year_visit_count[yr_ndx] = year_visit_count.get(yr_ndx, 0) + 1
                else:
                    gym_presence = "on"

        _LOGGER.debug(f"Found {len(visits)} since {self.last_sync}")

        gym_data["gymPresence"] = gym_presence
        gym_data["checkIns"] = check_ins
        gym_data["weeklyTotal"] = week_visits
        gym_data["monthlyTotal"] = month_visits
        gym_data["yearlyTotal"] = year_visits
        gym_data["monthlyVisitCount"] = month_visit_count
        gym_data["yearlyVisitCount"] = year_visit_count

        self.last_sync = sync_dt
        self.last_updated = last_updated
        return gym_data
