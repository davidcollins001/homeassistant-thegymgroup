"""Owlet integration coordinator class."""
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta

from pyrippleapi.exceptions import RippleConnectionError, RippleError
from pyrippleapi.generation_asset import GenerationAsset

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


def df(ts):
    return ts.isoformat(sep="T", timespec="seconds")


class GarminConnectDataUpdateCoordinator(DataUpdateCoordinator):
    """The Gym Group Data Update Coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the The Gym Group hub."""
        self.entry = entry
        self.hass = hass
        self.in_china = False

        country = self.hass.config.country
        if country == "CN":
            self.in_china = True

        self._api = Garmin(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], self.in_china)

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_UPDATE_INTERVAL
        )

    async def async_login(self):
        """Login to The Gym Group."""
        try:
            await self.hass.async_add_executor_job(self._api.login)
        except (
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            _LOGGER.error("Error occurred during The Gym Group login request: %s", err)
            return False
        except (GarminConnectConnectionError) as err:
            _LOGGER.error(
                "Connection error occurred during The Gym Group login request: %s", err
            )
            raise ConfigEntryNotReady from err
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Unknown error occurred during The Gym Group login request"
            )
            return False

        return True

    async def _async_update_data(self):
        """Fetch data from The Gym Group."""

        summary = {}
        body = {}
        alarms = {}
        gear = {}
        gear_stats = {}
        gear_defaults = {}
        activity_types = {}
        sleep_data = {}
        sleep_score = None
        hrv_data = {}
        hrvStatus = {"status": "UNKNOWN"}

        try:
            summary = await self.hass.async_add_executor_job(
                self._api.get_user_summary, date.today().isoformat()
            )
            _LOGGER.debug(f"Summary data: {summary}")

            body = await self.hass.async_add_executor_job(
                self._api.get_body_composition, date.today().isoformat()
            )
            _LOGGER.debug(f"Body data: {body}")

            activities = await self.hass.async_add_executor_job(
                self._api.get_activities_by_date,
                (date.today() - timedelta(days=7)).isoformat(),
                (date.today() + timedelta(days=1)).isoformat()
            )
            _LOGGER.debug(f"Activities data: {activities}")
            summary['lastActivities'] = activities

            badges = await self.hass.async_add_executor_job(
                self._api.get_earned_badges
            )
            _LOGGER.debug(f"Badges data: {badges}")
            summary['badges'] = badges

            alarms = await self.hass.async_add_executor_job(self._api.get_device_alarms)
            _LOGGER.debug(f"Alarms data: {alarms}")

            activity_types = await self.hass.async_add_executor_job(
                self._api.get_activity_types
            )
            _LOGGER.debug(f"Activity types data: {activity_types}")

            sleep_data = await self.hass.async_add_executor_job(
                self._api.get_sleep_data, date.today().isoformat())
            _LOGGER.debug(f"Sleep data: {sleep_data}")

            hrv_data = await self.hass.async_add_executor_job(
                self._api.get_hrv_data, date.today().isoformat())
            _LOGGER.debug(f"hrv data: {hrv_data}")
        except (
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
            GarminConnectConnectionError
        ) as error:
            _LOGGER.debug("Trying to relogin to The Gym Group")
            if not await self.async_login():
                raise UpdateFailed(error) from error
            return {}

        try:
            gear = await self.hass.async_add_executor_job(
                self._api.get_gear, summary[GEAR.USERPROFILE_ID]
            )
            _LOGGER.debug(f"Gear data: {gear}")

            tasks: list[Awaitable] = [
                self.hass.async_add_executor_job(
                    self._api.get_gear_stats, gear_item[GEAR.UUID]
                )
                for gear_item in gear
            ]
            gear_stats = await asyncio.gather(*tasks)
            _LOGGER.debug(f"Gear stats data: {gear_stats}")

            gear_defaults = await self.hass.async_add_executor_job(
                self._api.get_gear_defaults, summary[GEAR.USERPROFILE_ID]
            )
            _LOGGER.debug(f"Gear defaults data: {gear_defaults}")
        except:
            _LOGGER.debug("Gear data is not available")

        try:
            sleep_score = sleep_data["dailySleepDTO"]["sleepScores"]["overall"]["value"]
            _LOGGER.debug(f"Sleep score data: {sleep_score}")
        except KeyError:
            _LOGGER.debug("Sleep score data is not available")

        try:
            if hrv_data and "hrvSummary" in hrv_data:
                hrvStatus = hrv_data["hrvSummary"]
                _LOGGER.debug(f"HRV status: {hrvStatus} ")
        except KeyError:
            _LOGGER.debug("HRV data is not available")

        return {
            **summary,
            **body["totalAverage"],
            "nextAlarm": alarms,
            "gear": gear,
            "gear_stats": gear_stats,
            "activity_types": activity_types,
            "gear_defaults": gear_defaults,
            "sleepScore": sleep_score,
            "hrvStatus": hrvStatus,
        }


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
        self.last_sync = datetime.now()

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
            # sync current capacity
            gym_capacity = self.fetch(
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
                f"{start_date}&"
                f"endDate={df(datetime.now())}",
                session
            )

            gym_data, visits = await asyncio.gather(gym_capacity, gym_visit)

            check_ins = visits["checkIns"]
            if check_ins:
                _LOGGER.debug(f"Found {len(visits)} since {self.last_sync}")
                gym_data["checkIns"] = check_ins

        self.last_sync = datetime.now()
        return gym_data
