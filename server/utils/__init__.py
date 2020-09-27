# flake8: noqa

from datetime import datetime, timezone

from .jetri import Jetri
from .mongoconn import VTBiliDatabase
from .rotatingapi import RotatingAPIKey
from .twitchapi import TwitchHelix


def datetime_yt_parse(yt_time):
    try:
        yt_time = datetime.strptime(yt_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        yt_time = datetime.strptime(yt_time, "%Y-%m-%dT%H:%M:%SZ")
    yt_timestamp = int(round(yt_time.replace(tzinfo=timezone.utc).timestamp()))
    return yt_timestamp


def current_time():
    now = datetime.now(timezone.utc).timestamp()
    return int(round(now))
