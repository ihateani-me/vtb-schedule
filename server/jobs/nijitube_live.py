import asyncio
import logging
from typing import Any, Tuple

import aiohttp
import feedparser

from utils import (RotatingAPIKey, VTNijiDatabase, current_time,
                   datetime_yt_parse)

vtlog = logging.getLogger("jobs.nijitube_live")


async def check_for_doubles(dataset: list):
    repaired_data = []
    parsed_ids = []
    for data in dataset:
        if data["id"] not in parsed_ids:
            parsed_ids.append(data["id"])
            repaired_data.append(data)
    del parsed_ids
    return repaired_data


async def fetch_xmls(
    session: aiohttp.ClientSession, channel: str, aff: str, nn: int
) -> Tuple[Any, str, str, int]:
    parameter = {"channel_id": channel}
    async with session.get("https://www.youtube.com/feeds/videos.xml", params=parameter) as res:
        items_data = await res.text()
    return feedparser.parse(items_data), channel, aff, nn


async def fetch_apis(
    session: aiohttp.ClientSession, endpoint: str, param: dict, channel: str, aff: str
) -> Tuple[dict, str, str]:
    async with session.get(f"https://www.googleapis.com/youtube/v3/{endpoint}", params=param) as res:
        items_data = await res.json()
    return items_data, channel, aff


async def nijitube_video_feeds(
    DatabaseConn: VTNijiDatabase, channels_dataset: list, yt_api_key: RotatingAPIKey
):
    sessions = aiohttp.ClientSession(headers={"User-Agent": "VTNijiScheduler/0.1.0"})

    vtlog.info("Fetching saved live data...")
    try:
        youtube_lives_data: dict = await asyncio.wait_for(DatabaseConn.fetch_data("nijitube_live"), 15.0)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to fetch youtube live database, skipping run.")
        await sessions.close()
        return
    del youtube_lives_data["_id"]

    vtlog.info("Fetching all fetched video IDs...")
    fetched_video_ids = {}
    for channel, channel_data in youtube_lives_data.items():
        if channel not in fetched_video_ids:
            fetched_video_ids[channel] = []
        for video in channel_data:
            if video["id"] not in fetched_video_ids[channel]:
                fetched_video_ids[channel].append(video["id"])

    try:
        ended_video_ids = await asyncio.wait_for(DatabaseConn.fetch_data("nijitube_ended_ids"), 15.0)
        del ended_video_ids["_id"]
        for channel, channel_data in ended_video_ids.items():
            if channel not in fetched_video_ids:
                fetched_video_ids[channel] = []
            for video in channel_data:
                if video not in fetched_video_ids[channel]:
                    fetched_video_ids[channel].append(video)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.warning("Failed to fetch youtube ended id database, skipping run.")
        await sessions.close()
        return

    vtlog.info("Creating job task for xml files.")
    xmls_to_fetch = [
        fetch_xmls(sessions, chan["id"], chan["affs"], nn) for nn, chan in enumerate(channels_dataset)
    ]
    collected_videos_ids = {}
    vtlog.info("Firing xml fetching!")
    for xmls in asyncio.as_completed(xmls_to_fetch):
        feed_results, channel, affs, nn = await xmls

        fetched_videos = []
        if channel in fetched_video_ids:
            fetched_videos = fetched_video_ids[channel]

        vtlog.info(f"|=> Processing XMLs: {channels_dataset[nn]['name']}")
        video_ids = []
        for entry in feed_results.entries:
            ids_ = entry["yt_videoid"]
            if ids_ not in fetched_videos:
                video_ids.append(ids_)

        collected_videos_ids[channel + "//" + affs] = video_ids

    vtlog.info("Collected!")
    vtlog.info("Now creating tasks for a non-fetched Video IDs to the API.")

    video_to_fetch = []
    for chan_aff, videos in collected_videos_ids.items():
        chan, aff = chan_aff.split("//")
        if not videos:
            vtlog.warn(f"Skipping: {chan} since there's no video to fetch.")
            continue
        param = {
            "part": "snippet,liveStreamingDetails",
            "id": ",".join(videos),
            "key": yt_api_key.get(),
        }
        vtlog.info(f"|-- Processing: {chan}")
        video_to_fetch.append(fetch_apis(sessions, "videos", param, chan, aff))

    if not video_to_fetch:
        vtlog.warn("|== No video to fetch, bailing!")
        await sessions.close()
        return 0

    vtlog.info("Firing API fetching!")
    time_past_limit = current_time() - (6 * 60 * 60)
    for task in asyncio.as_completed(video_to_fetch):
        video_results, ch_id, ch_aff = await task
        if ch_id not in youtube_lives_data:
            youtube_lives_data[ch_id] = []
        if ch_id not in ended_video_ids:
            ended_video_ids[ch_id] = []
        vtlog.info(f"|== Parsing videos data for: {ch_id}")
        youtube_videos_data = youtube_lives_data[ch_id]
        for res_item in video_results["items"]:
            video_id = res_item["id"]
            if "liveStreamingDetails" not in res_item:
                # Assume normal video
                ended_video_ids[ch_id].append(video_id)
                continue
            snippets = res_item["snippet"]
            livedetails = res_item["liveStreamingDetails"]
            if not livedetails:
                # Assume normal video
                ended_video_ids[ch_id].append(video_id)
                continue
            broadcast_cnt = snippets["liveBroadcastContent"]
            if not broadcast_cnt:
                broadcast_cnt = "unknown"
            if broadcast_cnt not in ("live", "upcoming"):
                broadcast_cnt = "unknown"

            title = snippets["title"]
            channel = snippets["channelId"]
            start_time = 0
            if "scheduledStartTime" in livedetails:
                start_time = datetime_yt_parse(livedetails["scheduledStartTime"])
            if "actualStartTime" in livedetails:
                start_time = datetime_yt_parse(livedetails["actualStartTime"])
            thumbs = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

            dd_hell = {
                "id": video_id,
                "title": title,
                "status": broadcast_cnt,
                "startTime": start_time,
                "endTime": None,
                "group": ch_aff,
                "thumbnail": thumbs,
                "platform": "youtube",
            }
            if "actualEndTime" in livedetails:
                dd_hell["endTime"] = datetime_yt_parse(livedetails["actualEndTime"])
                dd_hell["status"] = "past"

            if dd_hell["status"] == "past" and time_past_limit >= dd_hell["endTime"]:
                vtlog.warning(f"Removing: {video_id} since it's way past the time limit.")
                ended_video_ids[ch_id].append(video_id)
                continue

            vtlog.info("Adding: {}".format(video_id))
            youtube_videos_data.append(dd_hell)

        youtube_lives_data[ch_id] = youtube_videos_data
        vtlog.info(f"|== Updating database ({ch_id})...")
        upd_data = {ch_id: youtube_videos_data}

        try:
            await asyncio.wait_for(DatabaseConn.update_data("nijitube_live", upd_data), 15.0)
        except asyncio.TimeoutError:
            await DatabaseConn.release()
            DatabaseConn.raise_error()
            vtlog.error(f"Failed to update live data for {ch_id}, timeout by 15s...")

    try:
        await asyncio.wait_for(DatabaseConn.update_data("nijitube_ended_ids", ended_video_ids), 15.0)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to update ended video ids, timeout by 15s...")

    vtlog.info("Closing sessions...")
    await sessions.close()


async def nijitube_live_heartbeat(
    DatabaseConn: VTNijiDatabase, affliates_dataset: dict, yt_api_key: RotatingAPIKey
):
    session = aiohttp.ClientSession(headers={"User-Agent": "VTNijiScheduler/0.1.0"})

    vtlog.info("Fetching live data...")

    try:
        youtube_lives_data = await asyncio.wait_for(DatabaseConn.fetch_data("nijitube_live"), 15.0)
        ended_video_ids = await asyncio.wait_for(DatabaseConn.fetch_data("nijitube_ended_ids"), 15.0)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to fetch youtube live database, skipping run.")
        await session.close()
        return
    del youtube_lives_data["_id"]

    videos_list = []
    videos_set = {}
    for cid, data in youtube_lives_data.items():
        for vd in data:
            if vd["status"] in ("unknown"):
                continue
            videos_list.append(vd["id"])
            videos_set[vd["id"]] = cid

    if not videos_list:
        vtlog.warn("No live/upcoming videos, bailing!")
        await session.close()
        return 0

    chunked_videos_list = [videos_list[i:i + 40] for i in range(0, len(videos_list), 40)]
    items_data_data = []
    for chunk_n, chunk_list in enumerate(chunked_videos_list, 1):
        vtlog.info(
            f"Checking heartbeat for chunk {chunk_n} out of {len(chunked_videos_list)} chunks"
        )
        param = {
            "part": "snippet,liveStreamingDetails",
            "id": ",".join(chunk_list),
            "key": yt_api_key.get(),
        }
        items_data, _, _ = await fetch_apis(session, "videos", param, "nullify", "nullify")
        items_data_data.extend(items_data["items"])
    await session.close()

    parsed_ids = {}
    vtlog.info("Parsing results...")
    time_past_limit = current_time() - (6 * 60 * 60)
    for res_item in items_data_data:
        video_id = res_item["id"]
        vtlog.info(f"|-- Checking {video_id} heartbeat...")
        snippets = res_item["snippet"]
        channel_id = snippets["channelId"]
        if channel_id not in ended_video_ids:
            ended_video_ids[channel_id] = []
        if "liveStreamingDetails" not in res_item:
            continue
        livedetails = res_item["liveStreamingDetails"]
        status_live = "upcoming"
        start_time = 0
        end_time = 0
        if "scheduledStartTime" in livedetails:
            start_time = datetime_yt_parse(livedetails["scheduledStartTime"])
        if "actualStartTime" in livedetails:
            status_live = "live"
            start_time = datetime_yt_parse(livedetails["actualStartTime"])
        if "actualEndTime" in livedetails:
            status_live = "past"
            end_time = datetime_yt_parse(livedetails["actualEndTime"])
        view_count = None
        if "concurrentViewers" in livedetails:
            view_count = livedetails["concurrentViewers"]
            try:
                view_count = int(view_count)
            except ValueError:
                pass
        thumbs = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        vtlog.info(f"|--> Update status for {video_id}: {status_live}")
        new_streams_data = []
        for data_streams in youtube_lives_data[channel_id]:
            if "group" not in data_streams:
                data_streams["group"] = affliates_dataset[channel_id]
            if data_streams["id"] == video_id:
                append_data = {
                    "id": data_streams["id"],
                    "title": snippets["title"],
                    "status": status_live,
                    "startTime": start_time,
                    "endTime": None,
                    "group": data_streams["group"],
                    "thumbnail": thumbs,
                    "platform": "youtube",
                }
                if view_count is not None:
                    append_data["viewers"] = view_count
                if status_live == "past":
                    append_data["endTime"] = end_time
                if status_live == "past" and time_past_limit >= end_time:
                    vtlog.warning(f"Removing: {video_id} since it's way past the time limit.")
                    ended_video_ids[channel_id].append(video_id)
                    continue
                new_streams_data.append(append_data)
            else:
                if data_streams["status"] == "past":
                    if time_past_limit >= data_streams["endTime"]:
                        vtlog.warning(f"Removing: {video_id} since it's way past the time limit.")
                        ended_video_ids[channel_id].append(video_id)
                        continue
                new_streams_data.append(data_streams)
        new_streams_data = await check_for_doubles(new_streams_data)
        youtube_lives_data[channel_id] = new_streams_data
        vtlog.info(f"|-- Updating heartbeat for channel {channel_id}...")
        try:
            await asyncio.wait_for(
                DatabaseConn.update_data("nijitube_live", {channel_id: new_streams_data}), 15.0
            )
        except asyncio.TimeoutError:
            await DatabaseConn.release()
            DatabaseConn.raise_error()
            vtlog.error(f"|--! Failed to update heartbeat for channel {channel_id}, timeout by 15s...")
        parsed_ids[video_id] = channel_id

    # Filter this if the video is privated.
    parsed_ids_keys = list(parsed_ids.keys())
    for video in videos_list:
        if video not in parsed_ids_keys:
            chan_id = videos_set[video]
            channel_data = youtube_lives_data[chan_id]
            new_channel_data = []
            for ch_vid in channel_data:
                if ch_vid["id"] != video:
                    new_channel_data.append(ch_vid)
                else:
                    if chan_id not in ended_video_ids:
                        ended_video_ids[chan_id] = []
                    ended_video_ids[chan_id].append(ch_vid["id"])
            vtlog.info(f"|-- Updating heartbeat filter for channel {chan_id}...")
            try:
                await asyncio.wait_for(
                    DatabaseConn.update_data("nijitube_live", {chan_id: new_channel_data}), 15.0
                )
            except asyncio.TimeoutError:
                await DatabaseConn.release()
                DatabaseConn.raise_error()
                vtlog.error(f"|--! Failed to update heartbeat for channel {chan_id}, timeout by 15s...")

    try:
        await asyncio.wait_for(DatabaseConn.update_data("nijitube_ended_ids", ended_video_ids), 15.0)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to update ended video ids, timeout by 15s...")
