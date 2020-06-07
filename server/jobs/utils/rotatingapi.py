import collections
import logging
from datetime import datetime, timezone


class RotatingAPIKey:
    """A class to rotate API key based on rotation rate"""

    def __init__(self, api_keys: list, minute_rate: int = 60):
        """Initialize class

        :param api_keys: A set of API keys on list
        :type api_keys: list
        :param minute_rate: A rotation rate in minutes, defaults to 60 minutes
        :type minute_rate: int, optional
        """
        self.logger = logging.getLogger("rotatingapi")
        self._api_keys = collections.deque(api_keys)
        self._kcount = len(api_keys)
        self._rate = minute_rate * 60
        self._next_rotate = (
            datetime.now(tz=timezone.utc).timestamp() + self._rate
        )

    def __check_time(self):
        current_time = datetime.now(tz=timezone.utc)
        if current_time.timestamp() >= self._next_rotate:
            ctext = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            self.logger.info("Rotating API key...")
            self._next_rotate = current_time.timestamp() + self._rate
            self.logger.info(f"Next API rotate: {ctext}")
            self._api_keys.rotate(-1)

    def get(self) -> str:
        if self._kcount > 1:
            self.__check_time()
        return self._api_keys[0]
