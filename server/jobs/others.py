import logging
from datetime import datetime

import aiohttp
import pytz
from .utils import VTBiliDatabase

import ujson

vtlog = logging.getLogger("others")


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


async def fetch_bili_calendar(VTBS_UIDS):
    vtlog.debug(f"Total Others BiliBili IDs: {len(VTBS_UIDS)}")
    vtubers_uids = ",".join(VTBS_UIDS)
    current_dt = datetime.now()
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
            current_utc = datetime.now(tz=pytz.timezone("UTC")).timestamp()
            if current_utc >= program["start_time"]:
                continue
            ch_name = users_info[str(program["ruid"])]["uname"]
            generate_id = (
                f"bili{program['subscription_id']}_{program['program_id']}"
            )
            m_ = {
                "id": generate_id,
                "room_id": program["room_id"],
                "title": program["title"],
                "startTime": program["start_time"],
                "channel": str(program["ruid"]),
                "channel_name": ch_name,
            }
            final_dataset.append(m_)
    vtlog.info("Final sorting and caching...")
    final_dataset.sort(key=lambda x: x["startTime"])
    vtlog.debug(f"Total schedule: {len(final_dataset)}")
    return final_dataset


async def others_main(DatabaseConn: VTBiliDatabase, dataset_path: str):
    with open(dataset_path, "r", encoding="utf-8") as fp:
        CHAN_BILIBILI = ujson.load(fp)

    CHAN_BILI_UIDS = [chan["uid"] for chan in CHAN_BILIBILI]
    vtlog.info("Fetching bili calendar data...")
    calendar_data = await fetch_bili_calendar(CHAN_BILI_UIDS)

    vtlog.info("Updating database...")
    upd_data = {"upcoming": calendar_data}
    await DatabaseConn.update_data("otherbili_data", upd_data)
