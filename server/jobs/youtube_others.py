import asyncio
import logging
import re
from datetime import datetime

import aiohttp
import feedparser
from .utils import VTBiliDatabase

import ujson


async def fetch_xmls(
    session: aiohttp.ClientSession, channel: str, nn: int
) -> dict:
    parameter = {"channel_id": channel}
    async with session.get(
        "https://www.youtube.com/feeds/videos.xml", params=parameter
    ) as res:
        items_data = await res.text()
    return feedparser.parse(items_data), channel, nn


async def fetch_apis(
    session: aiohttp.ClientSession, param: dict, channel: str
) -> dict:
    async with session.get(
        "https://www.googleapis.com/youtube/v3/videos", params=param
    ) as res:
        items_data = await res.json()
    return items_data, channel


async def youtube_video_feeds(
    DatabaseConn: VTBiliDatabase, dataset: str, yt_api_key: str
):
    vtlog = logging.getLogger("yt_videos_feeds")
    sessions = aiohttp.ClientSession(headers={"User-Agent": "VTHellAPI/0.4.0"})
    ytid_re = re.compile(r"yt\:video\:(?P<ids>.*)")

    vtlog.debug("Opening dataset")
    with open(dataset, "r", encoding="utf-8") as fp:
        channels_dataset = ujson.load(fp)

    vtlog.info("Fetching all fetched video IDs...")
    fetched_video_ids = await DatabaseConn.fetch_data("yt_other_videoids")
    fetched_video_ids: list = fetched_video_ids["ids"]
    youtube_lives_data = await DatabaseConn.fetch_data("yt_other_livedata")
    del youtube_lives_data["_id"]

    vtlog.info("Creating job task for xml files.")
    xmls_to_fetch = [
        fetch_xmls(sessions, chan["id"], nn)
        for nn, chan in enumerate(channels_dataset)
    ]
    collected_videos_ids = {}
    vtlog.info("Firing xml fetching!")
    for xmls in asyncio.as_completed(xmls_to_fetch):
        feed_results, channel, nn = await xmls

        vtlog.info(f"Processing XMLs: {channels_dataset[nn]['name']}")
        video_ids = []
        for entry in feed_results.entries:
            match_id = re.search(ytid_re, entry["id"])
            ids_ = match_id.group("ids")
            if ids_ not in fetched_video_ids:
                video_ids.append(ids_)

        collected_videos_ids[channel] = video_ids

    vtlog.info("Collected!")
    vtlog.info("Now creating tasks for a non-fetched Video IDs to the API.")

    video_to_fetch = []
    for chan, videos in collected_videos_ids.items():
        if not videos:
            vtlog.warn(f"Skipping: {chan} since there's no video to fetch.")
            continue
        param = {
            "part": "snippet,liveStreamingDetails",
            "id": ",".join(videos),
            "key": yt_api_key,
        }
        vtlog.info(f"|-- Processing: {chan}")
        video_to_fetch.append(fetch_apis(sessions, param, chan))

    if not video_to_fetch:
        vtlog.warn("|== No video to fetch, bailing!")
        await sessions.close()
        return 0

    vtlog.info("Firing API fetching!")
    for task in asyncio.as_completed(video_to_fetch):
        video_results, ch_id = await task
        if ch_id not in youtube_lives_data:
            youtube_lives_data[ch_id] = []
        vtlog.info(f"|== Parsing videos data for: {ch_id}")
        youtube_videos_data = youtube_lives_data[ch_id]
        for res_item in video_results["items"]:
            video_id = res_item["id"]
            fetched_video_ids.append(video_id)
            if "liveStreamingDetails" not in res_item:
                continue
            snippets = res_item["snippet"]
            livedetails = res_item["liveStreamingDetails"]
            if not livedetails:
                continue
            if "actualEndTime" in livedetails:
                continue
            if "liveBroadcastContent" not in snippets:
                continue
            broadcast_cnt = snippets["liveBroadcastContent"]
            if not broadcast_cnt:
                continue
            if broadcast_cnt not in ("live", "upcoming"):
                continue
            if "actualStartTime" in livedetails:
                continue

            title = snippets["title"]
            channel = snippets["channelId"]
            vtlog.info("Adding: {}".format(video_id))
            start_time = livedetails["scheduledStartTime"]
            if "actualStartTime" in livedetails:
                start_time = livedetails["actualStartTime"]
            try:
                dts = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                dts = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
            start_time_ts = int(round(dts.timestamp()))

            dd_hell = {
                "id": video_id,
                "title": title,
                "status": broadcast_cnt,
                "startTime": start_time_ts,
            }

            youtube_videos_data.append(dd_hell)

        youtube_lives_data[ch_id] = youtube_videos_data
        vtlog.warn(youtube_lives_data[ch_id])
        vtlog.info(f"|== Updating database ({ch_id})...")
        upd_data = {ch_id: youtube_videos_data}
        await DatabaseConn.update_data("yt_other_livedata", upd_data)

    vtlog.info("Updating fetched IDs database..")
    upd_data = {"ids": fetched_video_ids}
    await DatabaseConn.update_data("yt_other_videoids", upd_data)
    await sessions.close()


async def youtube_live_heartbeat(
    DatabaseConn: VTBiliDatabase, yt_api_key: str
):
    vtlog = logging.getLogger("yt_live_heartbeat")
    session = aiohttp.ClientSession(headers={"User-Agent": "VTHellAPI/0.5.0"})

    vtlog.info("Fetching live data...")

    youtube_lives_data = await DatabaseConn.fetch_data("yt_other_livedata")
    del youtube_lives_data["_id"]

    videos_list = []
    for cid, data in youtube_lives_data.items():
        videos_list.extend([v["id"] for v in data])

    if not videos_list:
        vtlog.warn("No live/upcoming videos, bailing!")
        await session.close()
        return 0

    vtlog.info(f"Checking heartbeat for {len(videos_list)} videos")
    param = {
        "part": "snippet,liveStreamingDetails",
        "id": ",".join(videos_list),
        "key": yt_api_key,
    }
    items_data, _ = await fetch_apis(session, param, "nullify")
    await session.close()

    vtlog.info(f"Parsing results...")
    for res_item in items_data["items"]:
        video_id = res_item["id"]
        vtlog.info(f"|-- Checking {video_id} heartbeat...")
        snippets = res_item["snippet"]
        channel_id = snippets["channelId"]
        if "liveStreamingDetails" not in res_item:
            continue
        livedetails = res_item["liveStreamingDetails"]
        new_streams_data = []
        status_live = "upcoming"
        override_start_time = None
        if "actualStartTime" in livedetails:
            status_live = "live"
            strt = livedetails["actualStartTime"]
            try:
                strt = datetime.strptime(strt, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                strt = datetime.strptime(strt, "%Y-%m-%dT%H:%M:%SZ")
            override_start_time = int(round(strt.timestamp()))
        if "actualEndTime" in livedetails:
            status_live = "delete"
        vtlog.info(f"|--> Update status for {video_id}: {status_live}")
        for data_streams in youtube_lives_data[channel_id]:
            if data_streams["id"] == video_id:
                if status_live != "delete":
                    start_t = (
                        override_start_time
                        if override_start_time
                        else data_streams["startTime"]
                    )
                    new_streams_data.append(
                        {
                            "id": data_streams["id"],
                            "title": data_streams["title"],
                            "status": status_live,
                            "startTime": start_t,
                        }
                    )
            else:
                new_streams_data.append(data_streams)
        youtube_lives_data[channel_id] = new_streams_data

    vtlog.info("|-- Updating database...")
    await DatabaseConn.update_data("yt_other_livedata", youtube_lives_data)
