import asyncio
from datetime import datetime, timezone

import aiohttp


class Jetri:
    """Jetri Connection Helper"""

    BASE_API = "https://api.holotools.app/"

    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self._sess = aiohttp.ClientSession(headers={"User-Agent": "VTBSchedule/0.9.0"}, loop=loop)

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

    def __filter_data(self, dataset: list) -> list:
        current_time = datetime.now(timezone.utc).timestamp()
        _parsed_data = []
        for data in dataset:
            if not data["yt_video_key"]:
                continue  # Is bilibili
            dict_data = {}
            dict_data["id"] = data["yt_video_key"]
            dict_data["title"] = data["title"]
            utc_time = data["live_schedule"].replace("Z", "")
            if data["live_start"]:
                utc_time = data["live_start"].replace("Z", "")
            try:
                parsed_date = (
                    datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S.%f")
                    .replace(tzinfo=timezone.utc)
                    .timestamp()
                )
            except ValueError:
                parsed_date = (
                    datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
                )
            parsed_date = int(parsed_date)

            if data["status"] == "upcoming":
                if current_time >= parsed_date:
                    continue
            if data["status"] == "live":
                dict_data["viewers"] = data["live_viewers"]

            dict_data["thumbnail"] = f"https://i.ytimg.com/vi/{dict_data['id']}/maxresdefault.jpg"

            dict_data["startTime"] = parsed_date
            dict_data["status"] = data["status"]
            dict_data["platform"] = "youtube"
            dict_data["channel"] = data["channel"]["yt_channel_id"]
            _parsed_data.append(dict_data)
        return _parsed_data

    async def _request_jet(self, endpoint):
        url = self.BASE_API + endpoint
        async with self._sess.get(url) as resp:
            results = await resp.json()
        return results

    async def fetch_lives(self):
        live_data = await self._request_jet("v1/live")
        lives, upcomings = (
            self.__filter_data(live_data["live"]),
            self.__filter_data(live_data["upcoming"]),
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
