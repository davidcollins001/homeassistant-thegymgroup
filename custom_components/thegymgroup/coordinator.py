"""Owlet integration coordinator class."""
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


def df(ts):
    return ts.isoformat(sep="T", timespec="seconds")


class TheGymGroupCoordinator(DataUpdateCoordinator):
    """Coordinator is responsible for querying the device at a specified route."""

    def __init__(self, hass: HomeAssistant, entry,
                 poll_interval=DEFAULT_UPDATE_INTERVAL):
        """Initialise a custom coordinator."""
        self.entry = entry
        self.last_sync = None

        super().__init__(hass, _LOGGER, name=DOMAIN,
                         update_interval=poll_interval,
                         update_method=self.async_refresh_data)

        self.base_url = "https://thegymgroup.netpulse.com/np"
        self.headers = {
            "accept": "application/json",
            "accept-encoding": "gzip",
            "connection": "Keep-Alive",
            "host": "thegymgroup.netpulse.com",
            "user-agent": "okhttp/3.12.3",
            "x-np-api-version": "1.5",
            "x-np-app-version": "6.0.1",
            "x-np-user-agent": ("clientType=MOBILE_DEVICE; devicePlatform=ANDROID; "
                                "deviceUid=; "
                                "applicationName=The Gym Group; "
                                "applicationVersion=5.0; "
                                "applicationVersionCode=38"),
        }

    async def async_login(self):
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

                cookie = resp.headers["Set-Cookie"]
                data = await resp.json()

        self.headers["cookie"] = cookie
        self.profile = data
        self.last_sync = None

        return True

    async def fetch(self, url, session):
        async with session.get(f"{self.base_url}/{url}", headers=self.headers) \
                as response:
            if response.status != 200:
                err = await response.text()
                _LOGGER.error(f"failed for {url}: {err}")
                raise UpdateFailed(f"failed for {url}: {err}")

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
                start_date = f"startDate={df(self.last_sync)}"

            # sync gym visits
            gym_visit = self.fetch(
                f"exercisers/{user_id}/check-ins/history?"
                f"{start_date}&endDate={df(datetime.now())}",
                session
            )

            gym_data, visits = await asyncio.gather(gym_occupancy, gym_visit)

            check_ins = visits["checkIns"]
            # last "check in" is always shown, ignore if it's already been processed
            # if check_ins and self.data and check_ins != self.data.get('checkIns'):
            if check_ins:
                last_check_in = datetime.fromisoformat(check_ins[-1]['checkInDate'])

                today = datetime.now().replace(hour=0, minute=0, second=0)
                if last_check_in > today - timedelta(days=1):
                    _LOGGER.debug(f"Found {len(visits)} since {self.last_sync}")
                    gym_data["checkIns"] = check_ins

        self.last_sync = datetime.now()
        return gym_data
