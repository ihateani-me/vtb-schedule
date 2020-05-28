# *-* charset: utf-8 *-*
# flake8: noqa

from .memcache import MemcachedBridge

# Import sanic_motor models
from .models import (
    ChannelsBiliDB,
    HoloBiliDB,
    NijiBiliDB,
    OtherBiliDB,
    OtherYTDB,
    TwitcastingDB,
    TwitchDB,
)

# Import sanic_openapi models
from .models import (
    BiliChannelsModel,
    BiliScheduleModel,
    TwitcastChannelModel,
    TwitcastLiveModel,
    TwitchChannelModel,
    TwitchLiveModel,
    YouTubeScheduleModel,
)

# Import all json dataset
from .dataset import *
