from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

from utils import udumps
from utils.dbconn import (fetch_channels, fetch_data, fetch_otherbili,
                          fetch_otheryt, otherbili_channels_data,
                          otheryt_channels_data, parse_uuids_args,
                          parse_youtube_channel_args, parse_youtube_live_args)
from utils.models import (BiliChannelsModel, BiliScheduleModel,
                          YouTubeChannelModel, YouTubeScheduleModel)

otherbp = Blueprint("Others", "/other", strict_slashes=True)


@otherbp.get("/upcoming")
@doc.summary("Upcoming Others VTubers BiliBili Streams")
@doc.description(
    "Fetch a list of upcoming streams from BiliBili for Other VTubers"
    ", updated every 4 minutes."
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
async def otherupcoming_api(request):
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        upcoming_results = await fetch_data("otherbili", fetch_otherbili)
    else:
        upcoming_results = {"upcoming": []}
    upcoming_results = await parse_uuids_args(request.args, upcoming_results)
    return json(
        {
            "upcoming": upcoming_results["upcoming"],
            "cached": True if not on_maintenance else False,
        },
        dumps=udumps,
        headers={"Cache-Control": "public, max-age=60, immutable"},
    )


@otherbp.get("/channels")
@doc.summary("Others Vtubers BiliBili Channel Stats")
@doc.description(
    "Fetch a list of channels stats, updated every 6 hours."
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
async def otherchan_api(request):
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        channel_res = await fetch_channels("ch_otherbili", otherbili_channels_data)
    else:
        channel_res = {"channels": []}
    return json(
        {"channels": channel_res["channels"], "cached": True if not on_maintenance else False},
        dumps=udumps,
    )


@otherbp.get("/youtube/live")
@doc.summary("Live/Upcoming Others VTubers YouTube Streams")
@doc.description(
    "Fetch a list of live/upcoming streams from YouTube for Other VTubers"
    ", updated every 1 minute for live data and 2 minutes for upcoming data.\n\n"
    "The results can be filtered by using Query parameters\n"
    "The query params can handle multiple values, separate them by using comma (,)\n"
    "For example: `/other/youtube/live?group=voms,others,honeystrap`\n\n"
    "Wrong parameters value will just be ignored and not gonna return error."
)
@doc.produces(
    {
        "live": doc.List(YouTubeScheduleModel),
        "upcoming": doc.List(YouTubeScheduleModel),
        "ended": doc.List(YouTubeScheduleModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of live/upcoming streams",
    content_type="application/json",
)
@doc.consumes(
    doc.String(
        name="fields",
        description="Filter fields that will be returned, separeted by comma",
        choices=[
            "id",
            "title",
            "status",
            "startTime",
            "endTime",
            "thumbnail",
            "viewers",
            "channel"
        ]
    ),
    location="query",
)
@doc.consumes(
    doc.String(
        name="group",
        description="Filter groups that will be returned, separeted by comma",
        choices=[
            "vtuberesports",
            "lupinusvg",
            "irisblackgames",
            "cattleyareginagames",
            "nanashi",
            "animare",
            "vapart",
            "honeystrap",
            "sugarlyric",
            "mahapanca",
            "vivid",
            "noripro",
            "hanayori",
            "voms",
            "others"
        ]
    ),
    location="query",
)
@doc.consumes(
    doc.String(
        name="status",
        description="Filter status (live/upcoming/ended) that will be returned, separeted by comma",
        choices=[
            "live",
            "upcoming",
            "ended",
        ]
    ),
    location="query",
)
async def upcoming_live_other_yt(request):
    logger.info(f"Requested {request.path} data")
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    if on_maintenance:
        return json({"live": [], "upcoming": [], "ended": [], "cached": False})
    live_data = await fetch_data("otheryt", fetch_otheryt)
    if not live_data:
        return json({"upcoming": [], "live": [], "ended": [], "cached": False})

    try:
        live_data = await parse_youtube_live_args(request.args, live_data)
    except Exception as e:
        logger.error(e)
        return json(
            {
                "error": "Malformed arguments"
            },
            dumps=udumps,
            status=400
        )

    live_data["cached"] = True
    return json(
        live_data,
        dumps=udumps
    )


@otherbp.get("/youtube/channels")
@doc.summary("Channels for Other VTubers YouTube")
@doc.description(
    "Fetch a list of Others VTubers YouTube channels info/statistics"
    ", updated every 6 hours.\n\n"
    "The results can be filtered by using Query parameters\n"
    "The query params can handle multiple values, separate them by using comma (,)\n"
    "For example: `/other/youtube/channels?group=voms,others,honeystrap`\n\n"
    "Wrong parameters value will just be ignored and not gonna return error."
)
@doc.consumes(
    doc.String(
        name="fields",
        description="Filter fields that will be returned, separeted by comma",
        choices=[
            "id",
            "name",
            "description",
            "publishedAt",
            "subscriberCount",
            "videoCount",
            "viewCount",
            "thumbnail",
        ]
    ),
    location="query",
)
@doc.consumes(
    doc.String(
        name="group",
        description="Filter groups that will be returned, separeted by comma",
        choices=[
            "vtuberesports",
            "lupinusvg",
            "irisblackgames",
            "cattleyareginagames",
            "nanashi",
            "animare",
            "vapart",
            "honeystrap",
            "sugarlyric",
            "mahapanca",
            "vivid",
            "noripro",
            "hanayori",
            "voms",
            "others"
        ]
    ),
    location="query",
)
@doc.produces(
    {
        "channels": doc.List(YouTubeChannelModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of channels",
    content_type="application/json",
)
async def channels_other_yt(request):
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        channel_res = await fetch_channels("ch_otheryt", otheryt_channels_data)
    else:
        channel_res = {"channels": []}
    channel_res = await parse_youtube_channel_args(request.args, channel_res)
    return json(
        {"channels": channel_res["channels"], "cached": True if not on_maintenance else False},
        dumps=udumps,
    )
