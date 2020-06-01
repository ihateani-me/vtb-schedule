from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

import ujson
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_nijibili,
    nijisanji_channels_data,
    parse_uuids_args,
)
from utils.models import BiliChannelsModel, BiliScheduleModel

nijibp = Blueprint("Nijisanji", "/nijisanji", strict_slashes=True)


@nijibp.get("/live")
@doc.summary("Live/Upcoming Nijisanji streams")
@doc.description(
    "Fetch a list of live/upcoming streams from Nijisanji/VirtuaReal VTubers"
    ", updated every 2/4 minutes via cronjob."
)
@doc.consumes(
    doc.String(
        name="uids",
        description="Filter upcoming results with User ID "
        "(support multiple id separated by comma)",
    ),
    location="query",
)
@doc.produces(
    {
        "live": doc.List(BiliScheduleModel),
        "upcoming": doc.List(BiliScheduleModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of upcoming streams",
    content_type="application/json",
)
async def nijiliveup_api(request):
    logger.info(f"Requested {request.path} data")
    niji_results = await fetch_data("nijibili", fetch_nijibili)
    upcoming_results = await parse_uuids_args(request.args, niji_results)
    return json(
        {
            "live": niji_results["live"],
            "upcoming": upcoming_results["upcoming"],
            "cached": True,
        },
        dumps=ujson.dumps,
        ensure_ascii=False,
        escape_forward_slashes=False,
    )


@nijibp.get("/channels")
@doc.summary("Nijisanji VLivers Channel Stats")
@doc.description(
    "Fetch a list of channels stats, updated every 6 hours via cronjob."
)
@doc.produces(
    {
        "channels": doc.List(BiliChannelsModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of channels stats",
    content_type="application/json",
)
async def nijichan_api(request):
    logger.info(f"Requested {request.path} data")
    channel_res = await fetch_channels("ch_niji", nijisanji_channels_data)
    return json(
        {
            "channels": channel_res["channels"],
            "cached": True
        },
        dumps=ujson.dumps,
        ensure_ascii=False,
        escape_forward_slashes=False,
    )
