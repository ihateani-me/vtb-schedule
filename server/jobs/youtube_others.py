import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Tuple

import aiohttp
import feedparser
from .utils import RotatingAPIKey, VTBiliDatabase

import ujson


async def fetch_xmls(
    session: aiohttp.ClientSession, channel: str, nn: int
) -> Tuple[Any, str, int]:
    parameter = {"channel_id": channel}
    async with session.get(
        "https://www.youtube.com/feeds/videos.xml", params=parameter
    ) as res:
        items_data = await res.text()
    return feedparser.parse(items_data), channel, nn


async def fetch_apis(
    session: aiohttp.ClientSession, endpoint: str, param: dict, channel: str
) -> Tuple[dict, str]:
    async with session.get(
        f"https://www.googleapis.com/youtube/v3/{endpoint}", params=param
    ) as res:
        items_data = await res.json()
    return items_data, channel


async def youtube_video_feeds(
    DatabaseConn: VTBiliDatabase, dataset: str, yt_api_key: RotatingAPIKey
):
    vtlog = logging.getLogger("yt_videos_feeds")
    sessions = aiohttp.ClientSession(
        headers={"User-Agent": "VTBSchedule/0.6.2"}
    )

    vtlog.debug("Opening dataset")
    with open(dataset, "r", encoding="utf-8") as fp:
        channels_dataset = ujson.load(fp)

    vtlog.info("Fetching all fetched video IDs...")
    fetched_video_ids = await DatabaseConn.fetch_data("yt_other_videoids")
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

        fetched_videos = []
        if channel in fetched_video_ids:
            fetched_videos = fetched_video_ids[channel]

        vtlog.info(f"|=> Processing XMLs: {channels_dataset[nn]['name']}")
        video_ids = []
        for entry in feed_results.entries:
            ids_ = entry["yt_videoid"]
            if ids_ not in fetched_videos:
                video_ids.append(ids_)
                fetched_videos.append(ids_)

        collected_videos_ids[channel] = video_ids
        vtlog.info(
            f"|=> Updating fetched IDs: {channels_dataset[nn]['name']}.."
        )
        await DatabaseConn.update_data(
            "yt_other_videoids", {channel: fetched_videos}
        )

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
            "key": yt_api_key.get(),
        }
        vtlog.info(f"|-- Processing: {chan}")
        video_to_fetch.append(fetch_apis(sessions, "videos", param, chan))

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
            # fetched_video_ids.append(video_id)
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
            start_time_ts = int(
                round(dts.replace(tzinfo=timezone.utc).timestamp())
            )
            thumbs = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

            dd_hell = {
                "id": video_id,
                "title": title,
                "status": broadcast_cnt,
                "startTime": start_time_ts,
                "thumbnail": thumbs,
                "platform": "youtube",
            }

            youtube_videos_data.append(dd_hell)

        youtube_lives_data[ch_id] = youtube_videos_data
        vtlog.warn(youtube_lives_data[ch_id])
        vtlog.info(f"|== Updating database ({ch_id})...")
        upd_data = {ch_id: youtube_videos_data}
        await DatabaseConn.update_data("yt_other_livedata", upd_data)

    vtlog.info("Closing sessions...")
    await sessions.close()


async def youtube_live_heartbeat(
    DatabaseConn: VTBiliDatabase, yt_api_key: RotatingAPIKey
):
    vtlog = logging.getLogger("yt_live_heartbeat")
    session = aiohttp.ClientSession(
        headers={"User-Agent": "VTBSchedule/0.6.2"}
    )

    vtlog.info("Fetching live data...")

    youtube_lives_data = await DatabaseConn.fetch_data("yt_other_livedata")
    del youtube_lives_data["_id"]

    videos_list = []
    videos_set = {}
    for cid, data in youtube_lives_data.items():
        for vd in data:
            videos_list.append(vd["id"])
            videos_set[vd["id"]] = cid

    if not videos_list:
        vtlog.warn("No live/upcoming videos, bailing!")
        await session.close()
        return 0

    vtlog.info(f"Checking heartbeat for {len(videos_list)} videos")
    param = {
        "part": "snippet,liveStreamingDetails",
        "id": ",".join(videos_list),
        "key": yt_api_key.get(),
    }
    items_data, _ = await fetch_apis(session, "videos", param, "nullify")
    await session.close()

    parsed_ids = {}
    vtlog.info(f"Parsing results...")
    for res_item in items_data["items"]:
        video_id = res_item["id"]
        vtlog.info(f"|-- Checking {video_id} heartbeat...")
        snippets = res_item["snippet"]
        channel_id = snippets["channelId"]
        if "liveStreamingDetails" not in res_item:
            continue
        livedetails = res_item["liveStreamingDetails"]
        status_live = "upcoming"
        strt = livedetails["scheduledStartTime"]
        if "actualStartTime" in livedetails:
            status_live = "live"
            strt = livedetails["actualStartTime"]
        if "actualEndTime" in livedetails:
            status_live = "delete"
        try:
            strt = datetime.strptime(strt, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            strt = datetime.strptime(strt, "%Y-%m-%dT%H:%M:%SZ")
        start_t = int(round(strt.replace(tzinfo=timezone.utc).timestamp()))
        thumbs = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        vtlog.info(f"|--> Update status for {video_id}: {status_live}")
        new_streams_data = []
        for data_streams in youtube_lives_data[channel_id]:
            if data_streams["id"] == video_id:
                if status_live != "delete":
                    new_streams_data.append(
                        {
                            "id": data_streams["id"],
                            "title": snippets["title"],
                            "status": status_live,
                            "startTime": start_t,
                            "thumbnail": thumbs,
                            "platform": "youtube",
                        }
                    )
            else:
                new_streams_data.append(data_streams)
        youtube_lives_data[channel_id] = new_streams_data
        parsed_ids[video_id] = channel_id

    vtlog.info("|= Filtering out some data...")
    parsed_ids_key = list(parsed_ids.keys())
    for video in videos_list:
        if video not in parsed_ids_key:
            chan_id = videos_set[video]
            channel_data = youtube_lives_data[chan_id]
            new_channel_data = []
            for vidchan in channel_data:
                if vidchan["id"] != video:
                    new_channel_data.append(vidchan)
            youtube_lives_data[chan_id] = new_channel_data

    vtlog.info("|-- Updating database...")
    await DatabaseConn.update_data("yt_other_livedata", youtube_lives_data)


async def youtube_channels(
    DatabaseConn: VTBiliDatabase, dataset: str, yt_api_key: RotatingAPIKey
):
    vtlog = logging.getLogger("yt_channels")
    sessions = aiohttp.ClientSession(
        headers={"User-Agent": "VTBSchedule/0.6.2"}
    )

    vtlog.debug("Opening dataset")
    with open(dataset, "r", encoding="utf-8") as fp:
        channels_dataset = ujson.load(fp)

    vtlog.info("Creating task for channels data.")
    channels_tasks = []
    for channel in channels_dataset:
        vtlog.info(f"|-> Adding {channel['name']}")
        param = {
            "part": "snippet,statistics",
            "id": channel["id"],
            "key": yt_api_key.get(),
        }
        channels_tasks.append(
            fetch_apis(sessions, "channels", param, channel["name"])
        )

    vtlog.info("Running all tasks...")
    final_channels_dataset = []
    for chan_task in asyncio.as_completed(channels_tasks):
        chan_data, chan_name = await chan_task
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
            "platform": "youtube",
        }

        final_channels_dataset.append(data)

    vtlog.info("Final sorting...")
    if final_channels_dataset:
        final_channels_dataset.sort(key=lambda x: x["name"])

    vtlog.info("Updating database...")
    upd_data = {"channels": final_channels_dataset}
    await DatabaseConn.update_data("yt_other_channels", upd_data)
    await sessions.close()
