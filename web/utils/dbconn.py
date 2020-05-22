from aiocache import Cache, cached
from aiocache.serializers import JsonSerializer
from sanic.log import logger

from .dataset import OTHER_YT_DATASET
from .models import (
    ChannelsBiliDB,
    HoloBiliDB,
    NijiBiliDB,
    OtherBiliDB,
    OtherYTDB,
)


@cached(
    key="holobili", ttl=180, serializer=JsonSerializer(),
)
async def fetch_holobili():
    try:
        logger.debug("Fetching (HoloLive) database...")
        data = await HoloBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"upcoming": [], "live": []}
    logger.info("Returning...")
    upcoming_data = []
    live_data = []
    for upcome in data["upcoming"]:
        upcome["webtype"] = "bilibili"
        upcoming_data.append(upcome)
    for livers in data["live"]:
        livers["webtype"] = "bilibili"
        live_data.append(livers)
    return {"upcoming": upcoming_data, "live": live_data}


@cached(
    key="nijibili", ttl=180, serializer=JsonSerializer(),
)
async def fetch_nijibili():
    try:
        logger.debug("Fetching (Nijisanji) database...")
        data = await NijiBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"upcoming": [], "live": []}
    logger.info("Returning...")
    upcoming_data = []
    live_data = []
    for upcome in data["upcoming"]:
        upcome["webtype"] = "bilibili"
        upcoming_data.append(upcome)
    for livers in data["live"]:
        livers["webtype"] = "bilibili"
        live_data.append(livers)
    return {"upcoming": upcoming_data, "live": live_data}


@cached(
    key="otherbili", ttl=180, serializer=JsonSerializer(),
)
async def fetch_otherbili():
    try:
        logger.debug("Fetching (Other) database...")
        data = await OtherBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"upcoming": []}
    logger.info("Returning...")
    upcoming_data = []
    for upcome in data["upcoming"]:
        upcome["webtype"] = "bilibili"
        upcoming_data.append(upcome)
    return {"upcoming": upcoming_data}


@cached(
    key="otheryt", ttl=60, serializer=JsonSerializer(),
)
async def fetch_otheryt():
    try:
        logger.debug("Fetching (Other) YT database...")
        data = await OtherYTDB.find_one({}, as_raw=True)
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {}
    logger.info("Returning...")
    final_proper = {}
    for kk, vv in data.items():
        if kk == "_id":
            continue
        final_proper[kk] = vv
    return final_proper


@cached(
    key="channels", ttl=7200, serializer=JsonSerializer(),
)
async def fetch_channels_data():
    try:
        logger.debug("Fetching channels database...")
        data = await ChannelsBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"hololive": [], "nijisanji": [], "other": [], "cached": False}
    logger.info("Returning...")
    return {
        "hololive": data["hololive"],
        "nijisanji": data["nijisanji"],
        "other": data["other"],
        "cached": True,
    }


@cached(
    key="otherytchan", ttl=7200, serializer=JsonSerializer(),
)
async def fetch_otheryt_channels():
    # try:
    logger.debug("Fetching channels database...")
    return {"data": OTHER_YT_DATASET}


cache = Cache(serializer=JsonSerializer())


async def fetch_data(keyname: str, fallback_func, recache=False):
    logger.debug("Trying to fetch data...")
    if recache:
        logger.debug("Recaching data as requested by user...")
        data = await fallback_func()
        return data
    try:
        data = await cache.get(keyname)
        if not data:
            logger.debug("No cache found, fetching to remote DB.")
            data = await fallback_func()
        logger.debug("Cache found, using cache...")
    except Exception:
        logger.debug("Failed fetching cache...")
        data = await fallback_func()
    return data


async def fetch_channels(vliver):
    logger.debug(f"Fetching {vliver} channels data...")
    try:
        vlivers_chan = await cache.get("channels")
        if not vlivers_chan:
            logger.debug("No cache found, fetching to remote DB.")
            vlivers_chan = await fetch_channels_data()
        logger.debug("Cache found, using cache...")
    except Exception:
        logger.debug("Failed fetching cache, fetching to remote db...")
        vlivers_chan = await fetch_channels_data()

    if vliver not in vlivers_chan:
        logger.warn("Unknown vliver data, returning empty array...")
        return {"channels": [], "cached": False}
    return {"channels": vlivers_chan[vliver], "cached": True}


async def fetch_yt_channels():
    logger.debug(f"Fetching others youtube channels data...")
    try:
        vlivers_chan = await cache.get("otherytchan")
        if not vlivers_chan:
            logger.debug("No cache found, fetching to remote DB.")
            vlivers_chan = await fetch_otheryt_channels()
        logger.debug("Cache found, using cache...")
    except Exception:
        logger.debug("Failed fetching cache, fetching to remote db...")
        vlivers_chan = await fetch_otheryt_channels()
    return vlivers_chan


async def parse_uuids_args(args, fetched_results):
    if not args:
        return fetched_results
    uids = args.get("uids", "")
    if not uids:
        return fetched_results
    if isinstance(uids, list):
        uids = uids[0]
    uids = uids.split(",")
    logger.debug(f"Using User IDs: {', '.join(uids)}")
    filtered_results = []
    for stream in fetched_results["upcoming"]:
        if stream["channel"] in uids:
            filtered_results.append(stream)
    return {"upcoming": filtered_results, "cached": True}
