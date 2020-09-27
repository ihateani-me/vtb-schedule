from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

from utils import udumps
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_twitcasting,
    twitcast_channels_data,
)
from utils.models import TwitcastChannelModel, TwitcastLiveModel

twitcastbp = Blueprint("Twitcasting", "/twitcasting", strict_slashes=True)


@twitcastbp.get("/live")
@doc.summary("Live Twitcasting VTubers Streams")
@doc.description(
    "Fetch a list of live streams from Twitcasting VTubers"
    ", updated every 1 minute."
)
@doc.produces(
    {
        "live": doc.List(TwitcastLiveModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of upcoming streams",
    content_type="application/json",
)
async def twitcast_live(request):
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        twitcast_res = await fetch_data("twitcastdata", fetch_twitcasting)
    else:
        twitcast_res = {"live": []}
    return json(
        {"live": twitcast_res["live"], "cached": True if not on_maintenance else False},
        dumps=udumps,
        headers={"Cache-Control": "public, max-age=60, immutable"},
    )


@twitcastbp.get("/channels")
@doc.summary("Twitcasting VTubers Channel Stats")
@doc.description(
    "Fetch a list of VTubers Twitcasting channels info/statistics"
    ", updated every 6 hours."
)
@doc.produces(
    {
        "channels": doc.List(TwitcastChannelModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of channels stats",
    content_type="application/json",
)
async def twitcast_chan(request):
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        channel_res = await fetch_channels("ch_twitcast", twitcast_channels_data)
    else:
        channel_res = {"channels": []}
    return json(
        {"channels": channel_res["channels"], "cached": True if not on_maintenance else False},
        dumps=udumps,
    )
