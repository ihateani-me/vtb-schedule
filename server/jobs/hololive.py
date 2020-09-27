import asyncio
import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from utils import VTBiliDatabase

vtlog = logging.getLogger("jobs.hololive")

HOLO_BILI_UIDS = [
    "389056211",
    "286179206",
    "20813493",
    "366690056",
    "9034870",
    "389856447",
    "336731767",
    "339567211",
    "389857131",
    "375504219",
    "389858027",
    "389858754",
    "389857640",
    "389859190",
    "332704117",
    "389862071",
    "412135222",
    "412135619",
    "454737600",
    "454733056",
    "454955503",
    "443305053",
    "443300418",
    "491474048",
    "491474049",
    "491474050",
    "491474051",
    "491474052",
    "427061218",
    "354411419",
    "456368455",
    "511613156",
    "511613155",
    "511613157",
    "456232604",
    "551114700",
    "350631685",
    "551114698",
    "647375261",
]


async def requests_data(url, params):
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"  # noqa: E501
    }
    vtlog.debug("\tOpening new session...")
    async with aiohttp.ClientSession(headers=head) as session:
        vtlog.debug("\tRequesting URL...")
        async with session.get(url, params=params) as resp:
            vtlog.debug("\tGetting results...")
            json_results = await resp.json()
    return json_results


async def fetch_bili_calendar():
    vtlog.debug(f"Total HoloLive BiliBili IDs: {len(HOLO_BILI_UIDS)}")
    vtubers_uids = ",".join(HOLO_BILI_UIDS)
    current_dt = datetime.now(timezone(timedelta(hours=8)))  # Use GMT+8.
    current_ym = current_dt.strftime("%Y-%m")
    current_d = current_dt.day

    vtlog.debug(f"Current date: {current_ym} -- {current_d}")
    api_endpoint = "https://api.live.bilibili.com/xlive/web-ucenter/v2/calendar/GetProgramList"  # noqa: E501
    api_params = {"type": 3, "year_month": current_ym, "ruids": vtubers_uids}

    vtlog.info("Requesting to API...")
    api_responses = await requests_data(api_endpoint, api_params)
    vtlog.info("Parsing results...")
    programs_info = api_responses["data"]["program_infos"]
    users_info = api_responses["data"]["user_infos"]
    date_keys = [int(key) for key in programs_info.keys()]
    date_keys = [date for date in date_keys if date >= current_d]
    vtlog.debug(f"Total date to parse: {len(date_keys)}")

    final_dataset = []
    for date in date_keys:
        for program in programs_info[str(date)]["program_list"]:
            current_utc = datetime.now(tz=timezone.utc).timestamp()
            if current_utc >= program["start_time"]:
                continue
            ch_name = users_info[str(program["ruid"])]["uname"]
            generate_id = f"bili{program['subscription_id']}_{program['program_id']}"
            m_ = {
                "id": generate_id,
                "room_id": program["room_id"],
                "title": program["title"],
                "startTime": program["start_time"],
                "channel": str(program["ruid"]),
                "channel_name": ch_name,
                "platform": "bilibili",
            }
            final_dataset.append(m_)
    vtlog.info("Final sorting and caching...")
    final_dataset.sort(key=lambda x: x["startTime"])
    vtlog.debug(f"Total schedule: {len(final_dataset)}")
    return final_dataset


async def hololive_main(DatabaseConn: VTBiliDatabase):
    vtlog.info("Fetching bili calendar data...")
    calendar_data = await fetch_bili_calendar()

    vtlog.info("Updating database...")
    upd_data = {"upcoming": calendar_data}
    try:
        await asyncio.wait_for(DatabaseConn.update_data("hololive_data", upd_data), 15.0)
    except asyncio.TimeoutError:
        await DatabaseConn.release()
        DatabaseConn.raise_error()
        vtlog.error("Failed to update upcoming data, timeout by 15s...")
