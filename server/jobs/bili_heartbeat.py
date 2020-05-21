import asyncio
import logging
from datetime import datetime

import aiohttp

from .utils import VTBiliDatabase, Jetri

CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"  # noqa: E501


async def fetch_room(session: aiohttp.ClientSession, room_id: str) -> dict:
    parameter = {"room_id": room_id}
    async with session.get(
        "https://api.live.bilibili.com/room/v1/Room/get_info", params=parameter
    ) as res:
        try:
            items_data = await res.json()
        except ValueError:
            return {}, room_id
        if res.status != 200:
            return {}, room_id
    return items_data["data"], room_id


async def holo_heartbeat(
    DatabaseConn: VTBiliDatabase, JetriConn: Jetri, room_dataset: dict
):
    vtlog = logging.getLogger("holo_heartbeat")
    session = aiohttp.ClientSession(headers={"User-Agent": CHROME_UA})

    vtlog.info("Fetching currently live from Jetri...")
    holo_liveyt, _ = await JetriConn.fetch_lives()
    holo_data: dict = room_dataset["holo"]

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
        start_time = int(round(datetime.strptime(
            room_data["live_time"] + " +0800", "%Y-%m-%d %H:%M:%S %z"
        ).timestamp()))
        gen_id = f"bili{room_id}_{start_time}"
        dd = {
            "id": gen_id,
            "room_id": int(room_id),
            "title": room_data["title"],
            "startTime": start_time,
            "channel": str(room_data["uid"]),
            "channel_name": holo_data[str(room_data["uid"])]["name"],
        }
        final_results.append(dd)

    if not final_results:
        vtlog.warn("No live currently happening, bailing!")
        await session.close()
        return 1

    collect_live_channels = []
    for vt in holo_liveyt:
        collect_live_channels.append(vt["channel"])

    vtlog.info("Parsing results...")
    finalized_data = []
    for result in final_results:
        if result["id"] not in holo_data:
            finalized_data.append(result)
            continue
        yt_ver_data = holo_data[result["id"]]
        if "id" in collect_live_channels:
            if yt_ver_data["id"] in collect_live_channels:
                vtlog.warn("Ignoring since this is just YouTube restream...")
                continue
        finalized_data.append(result)

    if finalized_data:
        finalized_data.sort(key=lambda x: x["startTime"])

    vtlog.info("Updating database...")
    upd_data = {"live": finalized_data, "cached": True}
    await DatabaseConn.update_data("live_data", upd_data)
    await session.close()


async def niji_heartbeat(
    DatabaseConn: VTBiliDatabase, JetriConn: Jetri, room_dataset: dict
):
    vtlog = logging.getLogger("niji_heartbeat")
    session = aiohttp.ClientSession(headers={"User-Agent": CHROME_UA})

    vtlog.info("Fetching currently live from Jetri...")
    niji_liveyt, _ = await JetriConn.fetch_lives_niji()
    niji_data: dict = room_dataset["niji"]

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
        start_time = int(round(datetime.strptime(
            room_data["live_time"] + " +0800", "%Y-%m-%d %H:%M:%S %z"
        ).timestamp()))
        gen_id = f"bili{room_id}_{start_time}"
        dd = {
            "id": gen_id,
            "room_id": int(room_id),
            "title": room_data["title"],
            "startTime": start_time,
            "channel": str(room_data["uid"]),
            "channel_name": niji_data[str(room_data["uid"])]["name"],
        }
        final_results.append(dd)

    if not final_results:
        vtlog.warn("No live currently happening, bailing!")
        await session.close()
        return 1

    collect_live_channels = []
    for vt in niji_liveyt:
        collect_live_channels.append(vt["channel"])

    vtlog.info("Parsing results...")
    finalized_data = []
    for result in final_results:
        if result["id"] not in niji_data:
            finalized_data.append(result)
            continue
        yt_ver_data = niji_data[result["id"]]
        if "id" in collect_live_channels:
            if yt_ver_data["id"] in collect_live_channels:
                vtlog.warn("Ignoring since this is just YouTube restream...")
                continue
        finalized_data.append(result)

    if finalized_data:
        finalized_data.sort(key=lambda x: x["startTime"])

    vtlog.info("Updating database...")
    upd_data = {"live": finalized_data, "cached": True}
    await DatabaseConn.update_data("live_niji_data", upd_data)
    await session.close()
