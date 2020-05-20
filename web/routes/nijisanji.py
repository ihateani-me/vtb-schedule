from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

import ujson
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_nijibili,
    parse_uuids_args,
)
from utils.models import BiliChannelsModel, BiliScheduleModel

nijibp = Blueprint("Nijisanji", "/nijisanji", strict_slashes=True)


@nijibp.get("/upcoming")
@doc.summary("Upcoming Nijisanji streams")
@doc.description(
    "Fetch a list of upcoming streams from Nijisanji/VirtuaReal VTubers"
    ", updated every 4 minutes via cronjob."
)
@doc.consumes(
    doc.String(
        name="uids",
        description="Filter results with User ID "
        "(support multiple id separated by comma)",
    ),
    location="query",
)
@doc.produces(
    {
        "upcoming": doc.List(BiliScheduleModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of upcoming streams",
    content_type="application/json",
)
async def nijiupcoming_api(request):
    logger.info(f"Requested {request.path} data")
    upcoming_results = await fetch_data("nijibili", fetch_nijibili)
    return json(
        await parse_uuids_args(request.args, upcoming_results),
        dumps=ujson.dumps,
        ensure_ascii=False,
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
    return json(
        await fetch_channels("nijisanji"),
        dumps=ujson.dumps,
        ensure_ascii=False,
    )
