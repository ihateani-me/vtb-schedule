from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from sanic_openapi import doc

from utils import udumps
from utils.dbconn import (
    fetch_channels,
    fetch_data,
    fetch_twitch,
    twitch_channels_data,
)
from utils.models import TwitchChannelModel, TwitchLiveModel

twitchbp = Blueprint("Twitch", "/twitch", strict_slashes=True)


@twitchbp.get("/live")
@doc.summary("Live Twitch VTubers Streams")
@doc.description(
    "Fetch a list of live streams from Twitch VTubers"
    ", updated every 1 minute."
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
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        twitch_res = await fetch_data("twitchdata", fetch_twitch)
    else:
        twitch_res = {"live": []}
    return json(
        {"live": twitch_res["live"], "cached": True if not on_maintenance else False},
        dumps=udumps,
        headers={"Cache-Control": "public, max-age=60, immutable"},
    )


@twitchbp.get("/channels")
@doc.summary("Twitch VTubers Channel Stats")
@doc.description(
    "Fetch a list of VTubers Twitch channels info/statistics"
    ", updated every 6 hours."
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
    on_maintenance = request.app.config["API_MAINTENANCE_MODE"]
    logger.info(f"Requested {request.path} data")
    if not on_maintenance:
        channel_res = await fetch_channels("ch_twitch", twitch_channels_data)
    else:
        channel_res = {"channels": []}
    return json(
        {"channels": channel_res["channels"], "cached": True if not on_maintenance else False},
        dumps=udumps,
    )
