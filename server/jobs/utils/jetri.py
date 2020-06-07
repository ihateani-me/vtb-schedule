import asyncio
from datetime import datetime, timezone

import aiohttp


class Jetri:
    """Jetri Connection Helper"""

    BASE_API = "https://api.jetri.co/"

    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self._sess = aiohttp.ClientSession(
            headers={"User-Agent": "VTBSchedule/0.6.1"}, loop=loop
        )

    async def close(self):
        """Close sessions"""
        if not self._sess.closed:
            await self._sess.close()

    def __filter_upcoming(self, upcoming_data):
        """Filter upcoming data from Jetri"""
        _filtered_data = []
        for upcome in upcoming_data:
            utc_time = datetime.now(timezone.utc).timestamp()
            start_time = upcome["startTime"]
            if not isinstance(start_time, int):
                start_time = int(start_time)
            if utc_time >= start_time:
                continue
            _filtered_data.append(upcome)
        return _filtered_data

    async def _request_jet(self, endpoint):
        url = self.BASE_API + endpoint
        async with self._sess.get(url) as resp:
            results = await resp.json()
        return results

    async def fetch_lives(self):
        live_data = await self._request_jet("live")
        lives, upcomings = (
            live_data["live"],
            self.__filter_upcoming(live_data["upcoming"]),
        )
        return lives, upcomings

    async def fetch_channels(self):
        channels_data = await self._request_jet("channels")
        return channels_data["channels"]

    async def fetch_lives_niji(self):
        live_data = await self._request_jet("nijisanji/live")
        lives, upcomings = (
            live_data["live"],
            self.__filter_upcoming(live_data["upcoming"]),
        )
        return lives, upcomings

    async def fetch_channels_niji(self):
        channels_data = await self._request_jet("nijisanji/channels")
        return channels_data["channels"]
