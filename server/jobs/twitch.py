import logging
from datetime import datetime, timezone

from .utils import TwitchHelix, VTBiliDatabase

TWITCH_USERNAMES = [
    "artia_hololive",
    "kanae_2434",
    "hiirosss",
    "MoarinVtuber",
    "kochou_momiji",
    "ShibuyaHAL",
    "SilverStarVT",
    "pakichi",
]


async def twitch_channels(
    DatabaseConn: VTBiliDatabase, TwitchConn: TwitchHelix
):
    vtlog = logging.getLogger("twitch_channels")
    vtlog.info("Fetching Twitch API...")
    twitch_results = await TwitchConn.fetch_channels(TWITCH_USERNAMES)

    vtlog.info("Parsing results...")
    channels_data = []
    for result in twitch_results:
        vtlog.info(f"|-- Parsing: {result['login']}")
        vtlog.info(f"|-- Fetching followers: {result['login']}")
        followers_data = await TwitchConn.fetch_followers(result["id"])

        data = {
            "id": result["login"],
            "user_id": result["id"],
            "name": result["display_name"],
            "description": result["description"],
            "thumbnail": result["profile_image_url"],
            "followerCount": followers_data["total"],
            "viewCount": result["view_count"],
        }

        channels_data.append(data)

    upd_data = {"twitch": channels_data}
    vtlog.info("Updating database...")
    await DatabaseConn.update_data("channel_data", upd_data)


async def twitch_heartbeat(
    DatabaseConn: VTBiliDatabase, TwitchConn: TwitchHelix
):
    vtlog = logging.getLogger("twitch_heartbeat")
    vtlog.info("Fetching Twitch API...")
    twitch_results = await TwitchConn.fetch_live_data(TWITCH_USERNAMES)

    if not twitch_results:
        vtlog.warn("No one is live right now, bailing...")
        return 1

    vtlog.info("Parsing results...")
    lives_data = []
    for result in twitch_results:
        start_time = result["started_at"]
        stream_id = f"twitch{result['id']}"

        start_utc = (
            datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )

        data = {
            "id": stream_id,
            "title": result["title"],
            "startTime": start_utc,
            "channel": result["user_name"],
            "channel_id": result["user_id"],
            "webtype": "twitch",
        }
        lives_data.append(data)

    upd_data = {"live": lives_data}
    vtlog.info("Updating database...")
    await DatabaseConn.update_data("other_twitch_live", upd_data)
