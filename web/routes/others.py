from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

import ujson
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_otherbili,
    fetch_otheryt,
    fetch_yt_channels,
    parse_uuids_args,
)
from utils.models import (
    BiliChannelsModel,
    BiliScheduleModel,
    YouTubeScheduleModel,
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
    return json(
        await fetch_channels("other"), dumps=ujson.dumps, ensure_ascii=False
    )


@otherbp.get("/yt/live")
@doc.summary("Upcoming Other VTubers YouTube streams")
@doc.description(
    "Fetch a list of upcoming streams from Other VTubers YouTube"
    ", updated every 3 minutes via cronjob."
)
@doc.produces(
    {
        "live": doc.List(YouTubeScheduleModel),
        "upcoming": doc.List(YouTubeScheduleModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of live/upcoming streams",
    content_type="application/json",
)
async def upcoming_live_other_yt(request):
    logger.info(f"Requested {request.path} data")
    live_data = await fetch_data("otheryt", fetch_otheryt)
    if not live_data:
        return json({"upcoming": [], "live": [], "cached": False})
    upcoming_data = []
    current_lives = []
    for channel, channel_data in live_data.items():
        for dataset in channel_data:
            data = {
                "id": dataset["id"],
                "title": dataset["title"],
                "channel": channel,
                "startTime": dataset["startTime"],
            }
            if dataset["status"] == "upcoming":
                upcoming_data.append(data)
            elif dataset["status"] == "live":
                current_lives.append(data)
    return json(
        {"live": current_lives, "upcoming": upcoming_data, "cached": True},
        dumps=ujson.dumps,
        ensure_ascii=False,
    )


@otherbp.get("/yt/channels")
@doc.summary("Channels for Other VTubers YouTube")
@doc.description(
    "Fetch a list of supported Other VTuber for YouTube version.\n"
    "Not all VTuber listed on `/other/channels` are available here."
)
@doc.produces(
    {
        "channels": doc.List(
            {
                "id": doc.String("YouTube Channel ID"),
                "name": doc.String("VTubers Name"),
                "affiliates": doc.String("Agency of the VTubers"),
            }
        ),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of channels",
    content_type="application/json",
)
async def upcoming_channels_other_yt(request):
    logger.info(f"Requested {request.path} data")
    vlivers_chan = await fetch_yt_channels()

    if not vlivers_chan:
        return json({"channels": [], "cached": False}, dumps=ujson.dumps)

    return json(
        {"channels": vlivers_chan["data"], "cached": True},
        dumps=ujson.dumps,
        ensure_ascii=False,
        indent=4,
    )
