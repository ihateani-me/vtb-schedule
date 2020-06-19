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
@doc.summary("Live Twitcasting streams")
@doc.description(
    "Fetch a list of live streams from available Twitcasting"
    ", updated every 1 minutes via cronjob."
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
    logger.info(f"Requested {request.path} data")
    twitcast_res = await fetch_data("twitcastdata", fetch_twitcasting)
    return json(
        {"live": twitcast_res["live"], "cached": True},
        dumps=udumps,
        headers={"Cache-Control": "public, max-age=60, immutable"},
    )


@twitcastbp.get("/channels")
@doc.summary("Twitcasting Channel Stats")
@doc.description(
    "Fetch a list of channels stats, updated every 6 hours via cronjob."
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
    logger.info(f"Requested {request.path} data")
    channel_res = await fetch_channels("ch_twitcast", twitcast_channels_data)
    return json(
        {"channels": channel_res["channels"], "cached": True},
        dumps=udumps,
        headers={"Cache-Control": "public, max-age=7200, immutable"},
    )
