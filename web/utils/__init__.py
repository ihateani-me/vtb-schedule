# *-* charset: utf-8 *-*
# flake8: noqa

from functools import partial

import ujson

udumps = partial(ujson.dumps, ensure_ascii=False, escape_forward_slashes=False)

from .memcache import MemcachedBridge

# Import sanic_motor models
from .models import (
    OtherYTChannelsDB,
    HoloBiliDB,
    NijiBiliDB,
    OtherBiliDB,
    OtherYTDB,
    TwitcastingDB,
    TwitcastingChannelsDB,
    TwitchDB,
    TwitchChannelsDB,
    NijiTubeChannels,
    NijiTubeLive,
)

# Import sanic_openapi models
from .models import (
    BiliChannelsModel,
    BiliScheduleModel,
    TwitcastChannelModel,
    TwitcastLiveModel,
    TwitchChannelModel,
    TwitchLiveModel,
    YouTubeChannelModel,
    YouTubeScheduleModel,
)

from .dbconn import (
    fetch_channels,
    fetch_data,
    fetch_holobili,
    fetch_nijibili,
    fetch_otherbili,
    fetch_otheryt,
    fetch_twitcasting,
    fetch_twitch,
    hololive_channels_data,
    nijisanji_channels_data,
    otherbili_channels_data,
    otheryt_channels_data,
    twitcast_channels_data,
    twitch_channels_data,
    fetch_nijitube_live,
    fetch_nijitube_channels,
    parse_youtube_live_args,
    parse_youtube_channel_args,
)
