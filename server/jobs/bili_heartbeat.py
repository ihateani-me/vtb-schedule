import asyncio
import logging
from datetime import datetime, timezone
from typing import Tuple

import aiohttp

from utils import Jetri, VTBiliDatabase

CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"  # noqa: E501
vtlog = logging.getLogger("jobs.bili_heartbeat")


async def fetch_room_hls(session: aiohttp.ClientSession, room_id: str) -> Tuple[dict, str]:
    parameter = {
        "cid": room_id,
        "quality": 4,
        "platform": "h5",
        "otype": "json",
    }
    async with session.get("https://api.live.bilibili.com/room/v1/Room/playUrl", params=parameter) as res:
        try:
            items_data = await res.json()
        except ValueError:
            return {}, room_id
        if res.status != 200:
            return {}, room_id
    if "data" not in items_data:
        return {}, room_id
    return items_data["data"], room_id


async def fetch_room(session: aiohttp.ClientSession, room_id: str) -> Tuple[dict, str]:
    parameter = {"room_id": room_id}
    async with session.get("https://api.live.bilibili.com/room/v1/Room/get_info", params=parameter) as res:
        try:
            items_data = await res.json()
        except ValueError:
            return {}, room_id
        if res.status != 200:
            return {}, room_id
    return items_data["data"], room_id


async def holo_heartbeat(DatabaseConn: VTBiliDatabase, JetriConn: Jetri, room_dataset: dict):
    session = aiohttp.ClientSession(headers={"User-Agent": CHROME_UA})

    vtlog.info("Fetching local youtube data...")
    holo_lives, holo_upcome = await JetriConn.fetch_lives()

    vtlog.info("Collecting live channels on youtube...")
    collect_live_channels = []
    for live_data in holo_lives:
        ch_id = live_data["channel"]
        if ch_id not in collect_live_channels:
            vtlog.debug(f"|--> Adding: {ch_id}")
            collect_live_channels.append(ch_id)
    for up_data in holo_upcome:
        ch_id = up_data["channel"]
        current_time = datetime.now(tz=timezone.utc).timestamp() - 300
        if current_time >= up_data["startTime"]:
            if ch_id not in collect_live_channels:
                vtlog.debug(f"|--> Adding: {ch_id}")
                collect_live_channels.append(ch_id)

    holo_data: dict = room_dataset["holo"]
    vtlog.info("Fetching ignored room data from database...")
    # await DatabaseConn.fetch_data("hololive_ignored")
    is_db_fetched = False
    try:
        db_holo_ignored: dict = await asyncio.wait_for(DatabaseConn.fetch_data("hololive_ignored"), 15.0)
        is_db_fetched = True
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to fetch Hololive Ignored database, using blank data.")
        db_holo_ignored = {"data": []}
    holo_ignored: list = db_holo_ignored["data"]

    vtlog.info("Creating tasks to check room status...")
    room_to_fetch = [fetch_room(session, room) for room in holo_data.keys()]
    vtlog.info("Firing API requests!")
    final_results = []
    for froom in asyncio.as_completed(room_to_fetch):
        room_data, room_id = await froom
        vtlog.debug(f"|-- Checking heartbeat for: {room_id}")
        if not room_data:
            vtlog.warn(f"|--! Failed fetching Room ID: {room_id} skipping")
            continue
        if room_data["live_status"] != 1:
            continue
        thumbnail = room_data["user_cover"]
        viewers = room_data["online"]
        start_time = int(
            round(datetime.strptime(room_data["live_time"] + " +0800", "%Y-%m-%d %H:%M:%S %z").timestamp())
        ) - (
            8 * 60 * 60
        )  # Set to UTC
        gen_id = f"bili{room_id}_{start_time}"
        if gen_id in holo_ignored:
            vtlog.warn(f"Ignoring {room_id} since it's an Ignored restream...")
            continue
        if str(room_id) in holo_data:
            holo_map = holo_data[str(room_id)]
            if "id" in holo_map and holo_map["id"] in collect_live_channels:
                vtlog.warn(f"Ignoring {room_id} since it's a YouTube restream...")
                if gen_id not in holo_ignored:
                    holo_ignored.append(gen_id)
                continue
        vtlog.info(f"Adding room_id: {room_id}")
        dd = {
            "id": gen_id,
            "room_id": int(room_id),
            "title": room_data["title"],
            "startTime": start_time,
            "channel": str(room_data["uid"]),
            "channel_name": holo_data[str(room_id)]["name"],
            "thumbnail": thumbnail,
            "viewers": viewers,
            "platform": "bilibili",
        }
        final_results.append(dd)

    if final_results:
        final_results.sort(key=lambda x: x["startTime"])

    vtlog.info("Updating database...")
    upd_data = {"live": final_results}
    upd_data2 = {"data": holo_ignored}
    try:
        await asyncio.wait_for(DatabaseConn.update_data("hololive_data", upd_data), 15.0)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to update Hololive Heartbeat data, timeout by 15s...")
    if is_db_fetched:
        try:
            await asyncio.wait_for(DatabaseConn.update_data("hololive_ignored", upd_data2), 15.0)
        except asyncio.TimeoutError:
            await DatabaseConn.release()
            DatabaseConn.raise_error()
            vtlog.error("Failed to update Hololive ignored database, timeout by 15s...")
    await session.close()


async def niji_heartbeat(DatabaseConn: VTBiliDatabase, VTNijiConn: VTBiliDatabase, room_dataset: dict):
    session = aiohttp.ClientSession(headers={"User-Agent": CHROME_UA})

    vtlog.info("Fetching currently live/upcoming data from VTNiji Database...")
    collect_live_channels: list = []
    try:
        niji_yt_puredata = await asyncio.wait_for(VTNijiConn.fetch_data("nijitube_live"), 15.0)
        del niji_yt_puredata["_id"]
        for channel_id, channel_data in niji_yt_puredata.items():
            for vtu in channel_data:
                current_time = datetime.now(tz=timezone.utc).timestamp() - 300
                if vtu["status"] == "live":
                    if channel_id not in collect_live_channels:
                        collect_live_channels.append(channel_id)
                elif vtu["status"] == "upcoming":
                    if current_time >= vtu["startTime"]:
                        if channel_id not in collect_live_channels:
                            collect_live_channels.append(channel_id)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to fetch live/upcoming data from VTNiji Database, timeout by 15s...")
    niji_data: dict = room_dataset["niji"]
    vtlog.info("Fetching ignored room data from database...")
    is_db_fetched = False
    try:
        db_niji_ignored: dict = await asyncio.wait_for(DatabaseConn.fetch_data("nijisanji_ignored"), 15.0)
        is_db_fetched = True
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to fetch Nijisanji Ignored database, using blank data.")
        db_niji_ignored = {"data": []}
    niji_ignored: list = db_niji_ignored["data"]

    vtlog.info("Creating tasks to check room status...")
    room_to_fetch = [fetch_room(session, room) for room in niji_data.keys()]
    vtlog.info("Firing API requests!")
    final_results = []
    for froom in asyncio.as_completed(room_to_fetch):
        room_data, room_id = await froom
        vtlog.debug(f"|-- Checking heartbeat for: {room_id}")
        if not room_data:
            vtlog.warn(f"|--! Failed fetching Room ID: {room_id} skipping")
            continue
        if room_data["live_status"] != 1:
            continue
        thumbnail = room_data["user_cover"]
        viewers = room_data["online"]
        start_time = int(
            round(datetime.strptime(room_data["live_time"] + " +0800", "%Y-%m-%d %H:%M:%S %z").timestamp())
        ) - (
            8 * 60 * 60
        )  # Set to UTC.
        gen_id = f"bili{room_id}_{start_time}"
        if gen_id in niji_ignored:
            vtlog.warn(f"Ignoring {room_id} since it's an Ignored restream...")
            continue
        if str(room_id) in niji_data:
            niji_map = niji_data[str(room_id)]
            if "id" in niji_map and niji_map["id"] in collect_live_channels:
                vtlog.warn(f"Ignoring {room_id} since it's a YouTube restream...")
                if gen_id not in niji_ignored:
                    niji_ignored.append(gen_id)
                continue
        # hls_list, _ = await fetch_room_hls(session, str(room_id))
        dd = {
            "id": gen_id,
            "room_id": int(room_id),
            "title": room_data["title"],
            "startTime": start_time,
            "channel": str(room_data["uid"]),
            "channel_name": niji_data[str(room_id)]["name"],
            "thumbnail": thumbnail,
            "viewers": viewers,
            "platform": "bilibili",
        }
        final_results.append(dd)

    if final_results:
        final_results.sort(key=lambda x: x["startTime"])

    vtlog.info("Updating database...")
    upd_data = {"live": final_results}
    upd_data2 = {"data": niji_ignored}
    try:
        await asyncio.wait_for(DatabaseConn.update_data("nijisanji_data", upd_data), 15.0)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to update Nijisanji Heartbeat data, timeout by 15s...")
    if is_db_fetched:
        try:
            await asyncio.wait_for(DatabaseConn.update_data("nijisanji_ignored", upd_data2), 15.0)
        except asyncio.TimeoutError:
            await DatabaseConn.release()
            DatabaseConn.raise_error()
            vtlog.error("Failed to update Nijisanji ignored database, timeout by 15s...")
    await session.close()
