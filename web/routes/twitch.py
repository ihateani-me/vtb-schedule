from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

import ujson
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_twitch,
)
from utils.models import TwitchChannelModel, TwitchLiveModel

twitchbp = Blueprint("Twitch", "/twitch", strict_slashes=True)


@twitchbp.get("/live")
@doc.summary("Live Twitch streams")
@doc.description(
    "Fetch a list of live streams from available Twitch VTubers"
    ", updated every 1 minutes via cronjob."
)
@doc.produces(
    {
        "live": doc.List(TwitchLiveModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of upcoming streams",
    content_type="application/json",
)
async def twitch_live(request):
    logger.info(f"Requested {request.path} data")
    twitch_res = await fetch_data("twitchdata", fetch_twitch)
    return json(
        {"live": twitch_res["live"], "cached": True},
        dumps=ujson.dumps,
        ensure_ascii=False,
        escape_forward_slashes=False,
    )


@twitchbp.get("/channels")
@doc.summary("Twitch Channel Stats")
@doc.description(
    "Fetch a list of channels stats, updated every 6 hours via cronjob."
)
@doc.produces(
    {
        "channels": doc.List(TwitchChannelModel),
        "cached": doc.Boolean(
            "Is the results cached or not?", True, "cached", choices=[True]
        ),
    },
    description="A list of channels stats",
    content_type="application/json",
)
async def twitch_chan(request):
    logger.info(f"Requested {request.path} data")
    return json(
        await fetch_channels("twitch"),
        dumps=ujson.dumps,
        ensure_ascii=False,
        escape_forward_slashes=False,
    )