from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

from utils import udumps
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_holobili,
    hololive_channels_data,
    parse_uuids_args,
)
from utils.models import BiliChannelsModel, BiliScheduleModel

holobp = Blueprint("Hololive", "/", strict_slashes=True)


@holobp.get("/live")
@doc.summary("Live/Upcoming HoloPro BiliBili Streams")
@doc.description(
    "Fetch a list of live/upcoming streams from BiliBili for HoloPro VTubers"
    ", updated every 2 minutes for live data and 4 minutes for upcoming data."
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
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        holo_results = await fetch_data("holobili", fetch_holobili)
    else:
        holo_results = {"live": [], "upcoming": []}
    upcoming_results = await parse_uuids_args(request.args, holo_results)
    return json(
        {
            "live": holo_results["live"],
            "upcoming": upcoming_results["upcoming"],
            "cached": True if not on_maintenance else False,
        },
        dumps=udumps,
        headers={"Cache-Control": "public, max-age=60, immutable"},
    )


@holobp.get("/channels")
@doc.summary("HoloPro Vtubers BiliBili Channel Stats")
@doc.description(
    "Fetch a list of HoloPro VTubers BiliBili channels info/statistics"
    ", updated every 6 hours."
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
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        channel_res = await fetch_channels("ch_holo", hololive_channels_data)
    else:
        channel_res = {"channels": []}
    return json(
        {"channels": channel_res["channels"], "cached": True if not on_maintenance else False},
        dumps=udumps,
    )
