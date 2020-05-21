import asyncio
import logging

import aiohttp
from .utils import VTBiliDatabase

import ujson

vtlog = logging.getLogger("channelsbili")


async def requests_data(url):
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"  # noqa: E501
    }
    vtlog.debug("\tOpening new session...")
    async with aiohttp.ClientSession(headers=head) as session:
        vtlog.debug("\tRequesting URL...")
        async with session.get(url) as resp:
            vtlog.debug("\tGetting results...")
            json_results = await resp.json()
    return json_results


async def find_channel_info(item_list, channel_data):
    channel = int(channel_data["uid"])
    cd = {}
    for item in item_list:
        if item["mid"] == channel:
            cd = item
            break
    return cd, channel_data["id"], channel_data["num"]


async def main_process_loop(channels_uids):
    final_dds_data = {}
    vtlog.info("Requsting to vtbs api...")
    vtbs_api_data = await requests_data("https://api.vtbs.moe/v1/info")

    hololivers = []
    nijisanji_vlivers = []
    other_vlivers = []
    vtlog.info("Creating tasks...")
    fetch_tasks = [
        find_channel_info(vtbs_api_data, ch) for ch in channels_uids
    ]
    vtlog.info("Running all tasks...")
    for task in asyncio.as_completed(fetch_tasks):
        channel_data, ident, nsort = await task
        if ident in ("hololive", "hololivecn", "holostars", "hololiveid"):
            hololivers.append(
                {
                    "id": str(channel_data["mid"]),
                    "room_id": str(channel_data["roomid"]),
                    "name": channel_data["uname"],
                    "description": channel_data["sign"],
                    "thumbnail": channel_data["face"],
                    "subscriberCount": channel_data["follower"],
                    "viewCount": channel_data["archiveView"],
                    "videoCount": channel_data["video"],
                    "live": True if channel_data["liveStatus"] != 0 else False,
                    "nsort": nsort,
                }
            )
        elif ident in (
            "virtuareal",
            "nijisanji",
            "nijisanjikr",
            "nijisanjiid",
            "nijisanjiin",
        ):
            nijisanji_vlivers.append(
                {
                    "id": str(channel_data["mid"]),
                    "room_id": str(channel_data["roomid"]),
                    "name": channel_data["uname"],
                    "description": channel_data["sign"],
                    "thumbnail": channel_data["face"],
                    "subscriberCount": channel_data["follower"],
                    "viewCount": channel_data["archiveView"],
                    "videoCount": channel_data["video"],
                    "live": True if channel_data["liveStatus"] != 0 else False,
                    "nsort": nsort,
                }
            )
        else:
            other_vlivers.append(
                {
                    "id": str(channel_data["mid"]),
                    "room_id": str(channel_data["roomid"]),
                    "name": channel_data["uname"],
                    "description": channel_data["sign"],
                    "thumbnail": channel_data["face"],
                    "subscriberCount": channel_data["follower"],
                    "viewCount": channel_data["archiveView"],
                    "videoCount": channel_data["video"],
                    "live": True if channel_data["liveStatus"] != 0 else False,
                    "nsort": nsort,
                }
            )

    vtlog.debug(f"Total Holo: {len(hololivers)}")
    vtlog.debug(f"Total Niji: {len(nijisanji_vlivers)}")
    vtlog.debug(f"Total Others: {len(other_vlivers)}")
    hololivers.sort(key=lambda x: x["nsort"])
    nijisanji_vlivers.sort(key=lambda x: x["nsort"])
    other_vlivers.sort(key=lambda x: x["nsort"])
    hololivers = [
        {x: d[x] for x in d if x not in {"nsort"}} for d in hololivers
    ]
    nijisanji_vlivers = [
        {x: d[x] for x in d if x not in {"nsort"}} for d in nijisanji_vlivers
    ]
    other_vlivers = [
        {x: d[x] for x in d if x not in {"nsort"}} for d in other_vlivers
    ]
    final_dds_data["hololive"] = hololivers
    final_dds_data["nijisanji"] = nijisanji_vlivers
    final_dds_data["other"] = other_vlivers

    return final_dds_data


async def update_channels_stats(
    DatabaseConn: VTBiliDatabase, dataset_set: list
):
    vtlog.info("Collecting channel UUIDs")
    channels_uids = []
    for chan in dataset_set:
        vtlog.debug(f"Opening: {chan}")
        with open(chan, "r", encoding="utf-8") as fp:
            dds = ujson.load(fp)
        vtlog.debug(f"Total data: {len(dds)}")
        for nn, dd in enumerate(dds):
            channels_uids.append({"id": dd["id"], "uid": dd["uid"], "num": nn})

    vtlog.info("Processing...")
    final_data = await main_process_loop(channels_uids)
    vtlog.info("Updating DB data...")
    await DatabaseConn.update_data("channel_data", final_data)
