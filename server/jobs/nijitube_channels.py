import asyncio
import logging
from typing import Tuple

import aiohttp

from utils import RotatingAPIKey, VTNijiDatabase

vtlog = logging.getLogger("jobs.nijitube_channels")


async def fetch_apis(
    session: aiohttp.ClientSession, endpoint: str, param: dict, channel: str, aff: str
) -> Tuple[dict, str, str]:
    async with session.get(f"https://www.googleapis.com/youtube/v3/{endpoint}", params=param) as res:
        items_data = await res.json()
    return items_data, channel, aff


async def nijitube_channels_data(
    DatabaseConn: VTNijiDatabase, channels_dataset: list, yt_api_key: RotatingAPIKey
):
    sessions = aiohttp.ClientSession(headers={"User-Agent": "VTNijiScheduler/0.1.0"})

    vtlog.info("Creating task for channels data.")
    channels_tasks = []
    for channel in channels_dataset:
        vtlog.info(f"|-> Adding {channel['name']}")
        param = {
            "part": "snippet,statistics",
            "id": channel["id"],
            "key": yt_api_key.get(),
        }
        channels_tasks.append(fetch_apis(sessions, "channels", param, channel["name"], channel["affs"]))

    vtlog.info("Running all tasks...")
    for chan_task in asyncio.as_completed(channels_tasks):
        chan_data, chan_name, chan_aff = await chan_task
        vtlog.info(f"|--> Processing: {chan_name}")

        if "items" not in chan_data:
            vtlog.warn(f"|--! Failed to fetch: {chan_name}")
            continue
        chan_data = chan_data["items"]
        if not chan_data:
            vtlog.warn(f"|--! Empty data on {chan_name}")
            continue
        chan_data = chan_data[0]
        if not chan_data:
            vtlog.warn(f"|--! Empty data on {chan_name}")
            continue

        chan_snip = chan_data["snippet"]
        chan_stats = chan_data["statistics"]

        ch_id = chan_data["id"]
        title = chan_snip["title"]
        desc = chan_snip["description"]
        pubat = chan_snip["publishedAt"]

        thumbs_data = chan_snip["thumbnails"]
        if "high" in thumbs_data:
            thumbs = thumbs_data["high"]["url"]
        elif "medium" in thumbs_data:
            thumbs = thumbs_data["medium"]["url"]
        else:
            thumbs = thumbs_data["default"]["url"]

        subscount = chan_stats["subscriberCount"]
        viewcount = chan_stats["viewCount"]
        vidcount = chan_stats["videoCount"]

        try:
            subscount = int(subscount)
            viewcount = int(viewcount)
            vidcount = int(vidcount)
        except ValueError:
            pass

        data = {
            "id": ch_id,
            "name": title,
            "description": desc,
            "publishedAt": pubat,
            "thumbnail": thumbs,
            "subscriberCount": subscount,
            "viewCount": viewcount,
            "videoCount": vidcount,
            "group": chan_aff,
            "platform": "youtube",
        }

        vtlog.info(f"Updating channels database for {ch_id}...")
        try:
            await asyncio.wait_for(DatabaseConn.update_data("nijitube_channels", {ch_id: data}), 15.0)
        except asyncio.TimeoutError:
            await DatabaseConn.release()
            DatabaseConn.raise_error()
            vtlog.error("Failed to update channels data, timeout by 15s...")

    await sessions.close()
