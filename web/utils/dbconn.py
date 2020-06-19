from aiocache import Cache, cached
from aiocache.serializers import JsonSerializer
from sanic.log import logger

from .models import (
    HoloBiliDB,
    NijiBiliDB,
    OtherBiliDB,
    OtherYTChannelsDB,
    OtherYTDB,
    TwitcastingDB,
    TwitchDB,
)


@cached(
    key="holobili", ttl=60, serializer=JsonSerializer(),
)
async def fetch_holobili() -> dict:
    try:
        logger.debug("Fetching (HoloLive) database...")
        data = await HoloBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"upcoming": [], "live": []}
    logger.info("Returning...")
    return {"live": data["live"], "upcoming": data["upcoming"]}


@cached(
    key="nijibili", ttl=60, serializer=JsonSerializer(),
)
async def fetch_nijibili() -> dict:
    try:
        logger.debug("Fetching (Nijisanji) database...")
        data = await NijiBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"upcoming": [], "live": []}
    logger.info("Returning...")
    return {"live": data["live"], "upcoming": data["upcoming"]}


@cached(
    key="otherbili", ttl=60, serializer=JsonSerializer(),
)
async def fetch_otherbili() -> dict:
    try:
        logger.debug("Fetching (Other) database...")
        data = await OtherBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"upcoming": []}
    logger.info("Returning...")
    return {"upcoming": data["upcoming"]}


@cached(
    key="otheryt", ttl=60, serializer=JsonSerializer(),
)
async def fetch_otheryt() -> dict:
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
    key="twitchdata", ttl=60, serializer=JsonSerializer(),
)
async def fetch_twitch() -> dict:
    try:
        logger.debug("Fetching Twitch database...")
        data = await TwitchDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"live": []}
    logger.info("Returning...")
    return {"live": data["live"]}


@cached(
    key="twitcastdata", ttl=60, serializer=JsonSerializer(),
)
async def fetch_twitcasting() -> dict:
    try:
        logger.debug("Fetching Twitcasting database...")
        data = await TwitcastingDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"live": []}
    logger.info("Returning...")
    return {"live": data["live"]}


@cached(key="ch_holo", ttl=7200, serializer=JsonSerializer())
async def hololive_channels_data() -> dict:
    try:
        logger.debug("Fetching (HoloLive) database...")
        data = await HoloBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    logger.info("Returning...")
    return {"channels": data["channels"]}


@cached(key="ch_niji", ttl=7200, serializer=JsonSerializer())
async def nijisanji_channels_data() -> dict:
    try:
        logger.debug("Fetching (Nijisanji) database...")
        data = await NijiBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    logger.info("Returning...")
    return {"channels": data["channels"]}


@cached(key="ch_otherbili", ttl=7200, serializer=JsonSerializer())
async def otherbili_channels_data() -> dict:
    try:
        logger.debug("Fetching (OtherBili) database...")
        data = await OtherBiliDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    logger.info("Returning...")
    return {"channels": data["channels"]}


@cached(
    key="ch_otheryt", ttl=7200, serializer=JsonSerializer(),
)
async def otheryt_channels_data() -> dict:
    try:
        logger.debug("Fetching (YT Channels) database...")
        data = await OtherYTChannelsDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    logger.info("Returning...")
    return {"channels": data["channels"]}


@cached(
    key="ch_twitcast", ttl=7200, serializer=JsonSerializer(),
)
async def twitcast_channels_data() -> dict:
    try:
        logger.debug("Fetching (Twitcasting) database...")
        data = await TwitcastingDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    logger.info("Returning...")
    return {"channels": data["channels"]}


@cached(
    key="ch_twitch", ttl=7200, serializer=JsonSerializer(),
)
async def twitch_channels_data() -> dict:
    try:
        logger.debug("Fetching (Twitch) database...")
        data = await TwitchDB.find_one()
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    logger.info("Returning...")
    return {"channels": data["channels"]}


cache = Cache(serializer=JsonSerializer())


async def fetch_data(
    keyname: str, fallback_func, recache: bool = False
) -> dict:
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


async def fetch_channels(keyname: str, fallback_func) -> dict:
    logger.debug("Trying to fetch channels data...")
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


async def parse_uuids_args(args: dict, fetched_results: dict) -> dict:
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
