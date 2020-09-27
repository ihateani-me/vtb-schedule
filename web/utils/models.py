from datetime import datetime

import pytz
from sanic_motor import BaseModel
from sanic_openapi import doc

MOTOR_DB = "vtbili"


class HoloBiliDB(BaseModel):
    __coll__ = "hololive_data"
    __dbkey__ = MOTOR_DB


class NijiBiliDB(BaseModel):
    __coll__ = "nijisanji_data"
    __dbkey__ = MOTOR_DB


class OtherBiliDB(BaseModel):
    __coll__ = "otherbili_data"
    __dbkey__ = MOTOR_DB


class OtherYTDB(BaseModel):
    __coll__ = "yt_other_livedata"
    __dbkey__ = MOTOR_DB


class OtherYTChannelsDB(BaseModel):
    __coll__ = "yt_other_channels"
    __dbkey__ = MOTOR_DB


class TwitchDB(BaseModel):
    __coll__ = "twitch_data"
    __dbkey__ = MOTOR_DB


class TwitchChannelsDB(BaseModel):
    __coll__ = "twitch_channels"
    __dbkey__ = MOTOR_DB


class TwitcastingDB(BaseModel):
    __coll__ = "twitcasting_data"
    __dbkey__ = MOTOR_DB


class TwitcastingChannelsDB(BaseModel):
    __coll__ = "twitcasting_channels"
    __dbkey__ = MOTOR_DB


class NijiTubeLive(BaseModel):
    __coll__ = "nijitube_live"
    __dbkey__ = MOTOR_DB


class NijiTubeChannels(BaseModel):
    __coll__ = "nijitube_channels"
    __dbkey__ = MOTOR_DB


class BiliScheduleModel:
    id = doc.String(
        "A ID that consist of subscriptions_id"
        ' and program_id with "bili" prefixes.',
        choices=["bili1234_9876"],
    )
    room_id = doc.Integer(
        "BiliBili Live Room ID the streamer will use.", choices=[12345678]
    )
    title = doc.String("The room/live title.")
    startTime = doc.Integer(
        "Scheduled/Real stream start time in UTC.",
        choices=[int(datetime.now(pytz.timezone("UTC")).timestamp())],
    )
    channel = doc.String(
        "BiliBili Channel/Space/User ID.", choices=["123456789"]
    )
    channel_name = doc.String("BiliBili Channel/Space/User name.")
    thumbnail = doc.String("Thumbnail of the stream.")
    viewers = doc.Integer("Peak viewers for this stream.")
    platform = doc.String(description="(Ignore this)", choices=["bilibili"])


class BiliChannelsModel:
    id = doc.String(
        "An User/Channel/Space BiliBili ID.", choices=["123456789"]
    )
    room_id = doc.String(
        "BiliBili Live Room ID the streamer will use.", choices=["12345678"]
    )
    name = doc.String("BiliBili Channel/Space/User name.")
    description = doc.String("The Channel Signature/Description.")
    thumbnail = doc.String("The Channel profile picture.")
    subscriberCount = doc.Integer("The channels subscription/followers count.")
    viewCount = doc.Integer("The channels views count.")
    videoCount = doc.Integer("The channels published/uploaded videos count.")
    live = doc.Boolean(
        "Is the channel currently live or not.", choices=[True, False]
    )
    platform = doc.String(description="(Ignore this)", choices=["bilibili"])


class YouTubeScheduleModel:
    id = doc.String("A youtube video ID")
    title = doc.String("The video title.")
    startTime = doc.Integer(
        "Scheduled/Real stream start time in UTC.",
        choices=[int(datetime.now(pytz.timezone("UTC")).timestamp())],
    )
    channel = doc.String("YouTube Channel ID.")
    status = doc.String("Status of streams", choices=["live", "upcoming", "past"])
    thumbnail = doc.String("Thumbnail of the stream.")
    viewers = doc.Integer("Current viewers for this stream.")
    group = doc.String("The livers group.")
    platform = doc.String(description="(Ignore this)", choices=["youtube"])


class YouTubeChannelModel:
    id = doc.String("A youtube channel ID")
    name = doc.String("The channel name.")
    description = doc.String("The channel description.")
    publishedAt = doc.String("The channel publication date.")
    subscriberCount = doc.Integer("The channel subscriber count.")
    videoCount = doc.Integer("The channel video/upload count.")
    viewCount = doc.Integer("The channel total views count.")
    thumbnail = doc.String("The channel profile picture.")
    group = doc.String("The livers group.")
    platform = doc.String(description="(Ignore this)", choices=["youtube"])


class TwitchLiveModel:
    id = doc.String("Twitch stream ID")
    title = doc.String("The stream title.")
    startTime = doc.Integer(
        "Scheduled stream start time in UTC.",
        choices=[int(datetime.now(pytz.timezone("UTC")).timestamp())],
    )
    channel = doc.String("Twitch channel login name or username.")
    channel_id = doc.String("Twitch channel user ID.")
    thumbnail = doc.String("Thumbnail of the stream.")
    platform = doc.String(description="(Ignore this)", choices=["twitch"])


class TwitchChannelModel:
    id = doc.String("Twitch username")
    user_id = doc.String("Twitch user id.")
    name = doc.String("Twitch channel name.")
    description = doc.String("The Channel Description.")
    thumbnail = doc.String("The Channel profile picture.")
    followerCount = doc.Integer("The channels followers count.")
    viewCount = doc.Integer("The channels views count.")
    platform = doc.String(description="(Ignore this)", choices=["twitch"])


class TwitcastLiveModel:
    id = doc.String("A twitcasting stream ID")
    title = doc.String("The stream title.")
    startTime = doc.Integer(
        "Scheduled/Real stream start time in UTC.",
        choices=[int(datetime.now(pytz.timezone("UTC")).timestamp())],
    )
    channel = doc.String("Twitcaster channel ID.")
    viewers = doc.Integer("Current viewers for this stream.")
    peakViewers = doc.Integer("Peak viewers for this stream.")
    platform = doc.String(description="(Ignore this)", choices=["twitcasting"])


class TwitcastChannelModel:
    id = doc.String("Twitcaster user id")
    name = doc.String("Twitcaster channel name.")
    description = doc.String("The Channel Description.")
    thumbnail = doc.String("The Channel profile picture.")
    followerCount = doc.Integer("The channels followers count.")
    level = doc.Integer("The channels level.")
    platform = doc.String(description="(Ignore this)", choices=["twitcasting"])
