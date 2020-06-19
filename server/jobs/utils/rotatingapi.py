import collections
import logging
from datetime import datetime, timezone
from typing import Union


class RotatingAPIKey:
    """A class to rotate API key based on rotation rate"""

    def __init__(self, api_keys: Union[str, list], minute_rate: int = 60):
        """Initialize Rotating API

        self._kcount: API key total for easier access.
        self._rate: the minute_rate * 60 (in seconds)
        self._next_rotate: current time + _rate

        **NOTE**:
        All of the variable used in this are not mean to be changed by user.

        :param api_keys: A set of API keys on list
        :type api_keys: list
        :param minute_rate: A rotation rate in minutes, defaults to 60 minutes
        :type minute_rate: int, optional
        """
        self.logger = logging.getLogger("rotatingapi")
        if isinstance(api_keys, str):
            api_keys = [api_keys]
        self._api_keys = collections.deque(api_keys)
        self._kcount = len(api_keys)
        self._rate = minute_rate * 60
        self._next_rotate = (
            datetime.now(tz=timezone.utc).timestamp() + self._rate
        )

    def __check_time(self):
        """Internal time checking, it will be run automatically if you have more
        than one API keys when you initialized the class.

        This is internal function and can't be called outside from the class.

        Rotation method:
        If the time already passed the next_rotate time it will rotate the key
        forward and set the next_rotate time with the applied rate

        Ex:
        Provided: ["api_a", "api_b", "api_c"]
        Next rotation (1): ["api_b", "api_c", "api_a"]
        Next rotation (2): ["api_c", "api_a", "api_b"]
        Next rotation (3/Full rotate): ["api_a", "api_b", "api_c"]
        """
        current_time = datetime.now(tz=timezone.utc)
        if current_time.timestamp() >= self._next_rotate:
            ctext = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            self.logger.info("Rotating API key...")
            self._next_rotate = current_time.timestamp() + self._rate
            self.logger.info(f"Next API rotate: {ctext}")
            self._api_keys.rotate(-1)

    def get(self) -> str:
        """Fetch the first API keys
        the first api keys will always be different since
        the rotation check are always called everytime this functioon
        are called.

        :return: API Keys
        :rtype: str
        """
        if self._kcount > 1:
            self.__check_time()
        return self._api_keys[0]
