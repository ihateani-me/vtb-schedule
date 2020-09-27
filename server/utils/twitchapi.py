import asyncio
import logging
from datetime import datetime, timezone

import aiohttp


class TwitchHelix:
    """A self-made API communicator for Twitch Helix"""

    BASE_URL = "https://api.twitch.tv/helix/"
    OAUTH_URL = "https://id.twitch.tv/oauth2/"

    def __init__(self, client_id, client_secret, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        self.logger = logging.getLogger("utils.twitchapi.TwitchHelix")
        self._bearer_token = None
        self._expires = 0
        self._cid = client_id
        self._csc = client_secret
        self._sess = aiohttp.ClientSession(
            headers={"User-Agent": "VTBSchedule/0.9.0"}, loop=loop
        )
        self._authorized = False

    async def close(self):
        if not self._sess.closed:
            if not self._bearer_token or self.__current() >= self._expires:
                await self.expire_token()
            await self._sess.close()

    def __current(self):
        return datetime.now().replace(tzinfo=timezone.utc).timestamp()

    async def _requests(self, methods, url, params, headers):
        param_url = ""
        if isinstance(params, dict):
            s_ = []
            for key, val in params.items():
                s_.append(f"{key}={val}")
            param_url = "&".join(s_)
        elif isinstance(params, list):
            param_url = "&".join(params)
        elif isinstance(params, str):
            param_url = params
        async with methods(f"{url}?{param_url}", headers=headers) as resp:
            results = await resp.json()
        return results

    async def _requests_no_head(self, methods, url, params):
        async with methods(url, params=params) as resp:
            try:
                results = await resp.json()
            except Exception:
                results = await resp.text()
        return results

    async def _get(self, url, params, headers=None):
        if headers:
            results = await self._requests(
                self._sess.get, url, params, headers
            )
        else:
            results = await self._requests_no_head(self._sess.get, url, params)
        return results

    async def _post(self, url, params, headers=None):
        if headers:
            results = await self._requests(
                self._sess.post, url, params, headers
            )
        else:
            results = await self._requests_no_head(
                self._sess.post, url, params
            )
        return results

    async def expire_token(self):
        params = {"client_id": self._cid, "token": self._bearer_token}
        if self._authorized:
            self.logger.info("De-Authorizing...")
            await self._post(self.OAUTH_URL + "revoke", params)
            self.logger.info("De-Authorized!")
            self._expires = 0
            self._bearer_token = None
            self._authorized = False

    async def authorize(self):
        params = {
            "client_id": self._cid,
            "client_secret": self._csc,
            "grant_type": "client_credentials",
        }

        self.logger.info("Authorizing...")
        res = await self._post(self.OAUTH_URL + "token", params)
        current_utc = self.__current()
        self._expires = current_utc + res["expires_in"]
        self._bearer_token = res["access_token"]
        self.logger.info("Authorized!")
        self._authorized = True

    async def fetch_live_data(self, usernames: list):
        if not self._authorized:
            self.logger.warn(
                "You're not authorized yet, requesting new bearer token..."
            )
            await self.authorize()
        if self.__current() >= self._expires:
            self.logger.warn("Token expired, rerequesting...")
            await self.authorize()

        headers = {
            "Authorization": "Bearer {}".format(self._bearer_token),
            "Client-ID": self._cid,
        }
        url_params = []
        url_params.append("first=100")
        for username in usernames:
            url_params.append(f"user_login={username}")
        results = await self._get(
            self.BASE_URL + "streams", url_params, headers
        )
        return results["data"]

    async def fetch_channels(self, usernames: list):
        if not self._authorized:
            self.logger.warn(
                "You're not authorized yet, requesting new bearer token..."
            )
            await self.authorize()
        if self.__current() >= self._expires:
            self.logger.warn("Token expired, rerequesting...")
            await self.authorize()

        headers = {
            "Authorization": "Bearer {}".format(self._bearer_token),
            "Client-ID": self._cid,
        }
        url_params = []
        for username in usernames:
            url_params.append(f"login={username}")
        results = await self._get(self.BASE_URL + "users", url_params, headers)
        return results["data"]

    async def fetch_followers(self, user_id: str):
        if not self._authorized:
            self.logger.warn(
                "You're not authorized yet, requesting new bearer token..."
            )
            await self.authorize()
        if self.__current() >= self._expires:
            self.logger.warn("Token expired, rerequesting...")
            await self.authorize()

        headers = {
            "Authorization": "Bearer {}".format(self._bearer_token),
            "Client-ID": self._cid,
        }
        url_params = [f"to_id={user_id}"]
        results = await self._get(
            self.BASE_URL + "users/follows", url_params, headers
        )
        return results
