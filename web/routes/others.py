from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

import ujson
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_otherbili,
    otherbili_channels_data,
    parse_uuids_args,
)
from utils.models import (
    BiliChannelsModel,
    BiliScheduleModel,
)

otherbp = Blueprint("Others", "/other", strict_slashes=True)


@otherbp.get("/upcoming")
@doc.summary('Upcoming "Others" streams')
@doc.description(
    "Fetch a list of upcoming streams from the Others VTubers list"
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
async def otheupcoming_api(request):
    logger.info(f"Requested {request.path} data")
    upcoming_results = await fetch_data("otherbili", fetch_otherbili)
    return json(
        await parse_uuids_args(request.args, upcoming_results),
        dumps=ujson.dumps,
        ensure_ascii=False,
        escape_forward_slashes=False,
    )


@otherbp.get("/channels")
@doc.summary("Other VLivers Channel Stats")
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
async def othechan_api(request):
    logger.info(f"Requested {request.path} data")
    channel_res = await fetch_channels("ch_otherbili", otherbili_channels_data)
    return json(
        {
            "channels": channel_res["channels"],
            "cached": True
        },
        dumps=ujson.dumps,
        ensure_ascii=False,
        escape_forward_slashes=False,
    )

