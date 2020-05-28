from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

import ujson
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_holobili,
    parse_uuids_args,
)
from utils.models import BiliChannelsModel, BiliScheduleModel

holobp = Blueprint("Hololive", "/", strict_slashes=True)


@holobp.get("/live")
@doc.summary("Live/Upcoming HoloLive streams")
@doc.description(
    "Fetch a list of live/upcoming streams from HoloLive VTubers"
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
async def hololiveup_api(request):
    logger.info(f"Requested {request.path} data")
    holo_results = await fetch_data("holobili", fetch_holobili)
    upcoming_results = await parse_uuids_args(request.args, holo_results)
    return json(
        {
            "live": holo_results["live"],
            "upcoming": upcoming_results["upcoming"],
            "cached": True,
        },
        dumps=ujson.dumps,
        ensure_ascii=False,
        escape_forward_slashes=False,
    )


@holobp.get("/channels")
@doc.summary("HoloLivers Channel Stats")
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
async def holochan_api(request):
    logger.info(f"Requested {request.path} data")
    return json(
        await fetch_channels("hololive"),
        dumps=ujson.dumps,
        ensure_ascii=False,
        escape_forward_slashes=False,
    )
