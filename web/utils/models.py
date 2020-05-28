from datetime import datetime

import pytz
from sanic_motor import BaseModel
from sanic_openapi import doc

MOTOR_DB = "vtbili"


class HoloBiliDB(BaseModel):
    __coll__ = "live_data"
    __motor_db__ = MOTOR_DB


class NijiBiliDB(BaseModel):
    __coll__ = "live_niji_data"
    __motor_db__ = MOTOR_DB


class OtherBiliDB(BaseModel):
    __coll__ = "live_other_data"
    __motor_db__ = MOTOR_DB


class OtherYTDB(BaseModel):
    __coll__ = "yt_other_livedata"
    __motor_db__ = MOTOR_DB


class ChannelsBiliDB(BaseModel):
    __coll__ = "channel_data"
    __motor_db__ = MOTOR_DB


class TwitchDB(BaseModel):
    __coll__ = "other_twitch_live"
    __motor_db__ = MOTOR_DB


class TwitcastingDB(BaseModel):
    __coll__ = "twitcasting_data"
    __motor_db__ = MOTOR_DB


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
        "Scheduled stream start time in UTC.",
        choices=[int(datetime.now(pytz.timezone("UTC")).timestamp())],
    )
    channel = doc.String(
        "BiliBili Channel/Space/User ID.", choices=["123456789"]
    )
    channel_name = doc.String("BiliBili Channel/Space/User name.")
    webtype = doc.String(description="(Ignore this)", choices=["bilibili"])


class YouTubeScheduleModel:
    id = doc.String("A youtube video ID")
    title = doc.String("The video title.")
    startTime = doc.Integer(
        "Scheduled stream start time in UTC.",
        choices=[int(datetime.now(pytz.timezone("UTC")).timestamp())],
    )
    channel = doc.String("YouTube Channel ID.")


class TwitcastLiveModel:
    id = doc.String("A twitcasting stream ID")
    title = doc.String("The stream title.")
    startTime = doc.Integer(
        "Scheduled stream start time in UTC.",
        choices=[int(datetime.now(pytz.timezone("UTC")).timestamp())],
    )
    channel = doc.String("Twitcaster channel ID.")
    webtype = doc.String(description="(Ignore this)", choices=["twitcasting"])


class TwitchLiveModel:
    id = doc.String("Twitch stream ID")
    title = doc.String("The stream title.")
    startTime = doc.Integer(
        "Scheduled stream start time in UTC.",
        choices=[int(datetime.now(pytz.timezone("UTC")).timestamp())],
    )
    channel = doc.String("Twitch channel login name or username.")
    channel_id = doc.String("Twitch channel user ID.")
    webtype = doc.String(description="(Ignore this)", choices=["twitch"])


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


class TwitchChannelModel:
    id = doc.String("Twitch username")
    user_id = doc.String("Twitch user id.")
    name = doc.String("Twitch channel name.")
    description = doc.String("The Channel Description.")
    thumbnail = doc.String("The Channel profile picture.")
    followerCount = doc.Integer("The channels followers count.")
    viewCount = doc.Integer("The channels views count.")


class TwitcastChannelModel:
    id = doc.String("Twitcaster user id")
    name = doc.String("Twitcaster channel name.")
    description = doc.String("The Channel Description.")
    thumbnail = doc.String("The Channel profile picture.")
    followerCount = doc.Integer("The channels followers count.")
    level = doc.Integer("The channels level.")
