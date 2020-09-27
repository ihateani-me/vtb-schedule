from urllib.parse import unquote_plus

from aiocache import Cache, cached
from aiocache.serializers import JsonSerializer
from sanic.log import logger

from .models import (HoloBiliDB, NijiBiliDB, NijiTubeChannels,
                     NijiTubeLive, OtherBiliDB, OtherYTChannelsDB, OtherYTDB,
                     TwitcastingChannelsDB, TwitcastingDB, TwitchChannelsDB,
                     TwitchDB)


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
        data = await OtherYTChannelsDB.find_one({}, as_raw=True)
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    channels_res = []
    for channel, channel_data in data.items():
        if channel == "_id":
            continue
        channels_res.append(channel_data)
    logger.info("Returning...")
    return {"channels": channels_res}


@cached(
    key="ch_twitcast", ttl=7200, serializer=JsonSerializer(),
)
async def twitcast_channels_data() -> dict:
    try:
        logger.debug("Fetching (Twitcasting) database...")
        data = await TwitcastingChannelsDB.find_one({}, as_raw=True)
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    channels_res = []
    for channel, channel_data in data.items():
        if channel == "_id":
            continue
        channels_res.append(channel_data)
    logger.info("Returning...")
    return {"channels": channels_res}


@cached(
    key="ch_twitch", ttl=7200, serializer=JsonSerializer(),
)
async def twitch_channels_data() -> dict:
    try:
        logger.debug("Fetching (Twitch) database...")
        data = await TwitchChannelsDB.find_one({}, as_raw=True)
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    channels_res = []
    for channel, channel_data in data.items():
        if channel == "_id":
            continue
        channels_res.append(channel_data)
    logger.info("Returning...")
    return {"channels": channels_res}


@cached(
    key="nijitube_live", ttl=60, serializer=JsonSerializer(),
)
async def fetch_nijitube_live() -> dict:
    try:
        logger.debug("Fetching (NijiTube) YT database...")
        data = await NijiTubeLive.find_one({}, as_raw=True)
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
    key="nijitube_channels", ttl=7200, serializer=JsonSerializer(),
)
async def fetch_nijitube_channels() -> dict:
    try:
        logger.debug("Fetching (NijiTube Channels) database...")
        data = await NijiTubeChannels.find_one({}, as_raw=True)
    except Exception as e:
        logger.debug(e)
        logger.debug("Failed to fetch database, returning...")
        return {"channels": []}
    channels_res = []
    for channel, channel_data in data.items():
        if channel == "_id":
            continue
        channels_res.append(channel_data)
    logger.info("Returning...")
    return {"channels": channels_res}


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


def filter_empty(data: list) -> list:
    return [d for d in data if d]


async def parse_youtube_live_args(args: dict, fetched_results: dict) -> dict:
    filtered_live = []
    filtered_upcoming = []
    filtered_ended = []

    groups = args.get("group", "")
    groups = filter_empty(unquote_plus(groups).split(","))
    statuses = args.get("status", "")
    statuses = filter_empty(unquote_plus(statuses).split(","))
    fields = args.get("fields", "")
    fields = filter_empty(unquote_plus(fields).split(","))
    all_fields_keys = [
        "id", "title", "status", "startTime", "thumbnail", "endTime", "viewers", "channel"
    ]
    add_upcome = True
    add_lives = True
    add_ended = True
    if statuses:
        if "live" not in statuses:
            add_lives = False
        if "upcoming" not in statuses:
            add_upcome = False
        if "ended" not in statuses:
            add_ended = False
    if not groups:
        groups = [
            "vtuberesports",
            "nanashi",
            "others",
            "mahapanca",
            "vivid",
            "noripro",
            "voms",
            "hanayori",
            "kizunaai",
            "nijisanji",
        ]
    if not fields:
        fields = all_fields_keys
    logger.info(f"Groups set: {groups}")
    logger.info(f"Fields set: {fields}")
    logger.info(f"Live: {add_lives} || Upcoming: {add_upcome} || Ended: {add_ended}")

    groups_mappings = {
        "nijisanji": ["nijisanjijp", "nijisanjikr", "nijisanjiid", "nijisanjien"],
        "nijisanjikr": ["nijisanjikr"],
        "nijisanjijp": ["nijisanjijp"],
        "nijisanjien": ["nijisanjien"],
        "nijisanjiid": ["nijisanjiid"],
        "nijisanjiworld": ["nijisanjikr", "nijisanjiid", "nijisanjien"],
        "vtuberesports": ["irisbg", "cattleyarg", "lupinusvg"],
        "lupinusvg": ["lupinusvg"],
        "irisblackgames": ["irisbg"],
        "cattleyareginagames": ["cattleyarg"],
        "nanashi": ["vapart", "animare", "honeystrap", "sugarlyric"],
        "animare": ["animare"],
        "vapart": ["vapart"],
        "honeystrap": ["honeystrap"],
        "sugarlyric": ["sugarlyric"],
        "others": ["entum", "solotuber", "solovtuber", "paryiproject", "vic", "dotlive", "vgaming"],
        "mahapanca": ["mahapanca"],
        "vivid": ["vivid"],
        "noripro": ["noripro"],
        "hanayori": ["hanayori"],
        "voms": ["voms"],
        "kizunaai": ["kizunaai"],
    }

    logger.info("Filtering results...")
    for ch_id, streams in fetched_results.items():
        for stream in streams:
            stream["channel"] = ch_id
            for group in groups:
                groups_map = groups_mappings.get(group)
                if groups_map is not None:
                    if stream["group"] in groups_map:
                        if stream["status"] == "live":
                            filtered_live.append(stream)
                        elif stream["status"] == "upcoming":
                            filtered_upcoming.append(stream)
                        elif stream["status"] == "past":
                            filtered_ended.append(stream)

    key_to_del = []
    for field in all_fields_keys:
        if field not in fields:
            key_to_del.append(field)
    for live_data in filtered_live:
        for kbye in key_to_del:
            try:
                del live_data[kbye]
            except KeyError:
                pass
    for live_data in filtered_upcoming:
        for kbye in key_to_del:
            try:
                del live_data[kbye]
            except KeyError:
                pass
    for live_data in filtered_ended:
        for kbye in key_to_del:
            try:
                del live_data[kbye]
            except KeyError:
                pass

    if "startTime" not in key_to_del:
        filtered_live.sort(key=lambda x: x["startTime"])
        filtered_upcoming.sort(key=lambda x: x["startTime"])
    if "endTime" not in key_to_del:
        filtered_ended.sort(key=lambda x: x["endTime"])

    return_data = {}
    if add_lives:
        return_data["live"] = filtered_live
    if add_upcome:
        return_data["upcoming"] = filtered_upcoming
    if add_ended:
        return_data["ended"] = filtered_ended

    return return_data


async def parse_youtube_channel_args(args: dict, fetched_results: dict) -> dict:
    groups_mappings = {
        "nijisanji": ["nijisanjijp", "nijisanjikr", "nijisanjiid", "nijisanjien"],
        "nijisanjikr": ["nijisanjikr"],
        "nijisanjijp": ["nijisanjijp"],
        "nijisanjien": ["nijisanjien"],
        "nijisanjiid": ["nijisanjiid"],
        "nijisanjiworld": ["nijisanjikr", "nijisanjiid", "nijisanjien"],
        "vtuberesports": ["irisbg", "cattleyarg", "lupinusvg"],
        "lupinusvg": ["lupinusvg"],
        "irisblackgames": ["irisbg"],
        "cattleyareginagames": ["cattleyarg"],
        "nanashi": ["vapart", "animare", "honeystrap", "sugarlyric"],
        "animare": ["animare"],
        "vapart": ["vapart"],
        "honeystrap": ["honeystrap"],
        "sugarlyric": ["sugarlyric"],
        "others": ["entum", "solotuber", "solovtuber", "paryiproject", "vic", "dotlive", "vgaming"],
        "mahapanca": ["mahapanca"],
        "vivid": ["vivid"],
        "noripro": ["noripro"],
        "hanayori": ["hanayori"],
        "voms": ["voms"],
        "kizunaai": ["kizunaai"],
    }

    groups = args.get("group", "")
    groups = filter_empty(unquote_plus(groups).split(","))
    fields = args.get("fields", "")
    fields = filter_empty(unquote_plus(fields).split(","))
    all_fields_keys = [
        "id", "name", "description", "publishedAt", "subscriberCount", "videoCount", "viewCount", "thumbnail"
    ]
    if not groups:
        groups = [
            "vtuberesports",
            "nanashi",
            "others",
            "mahapanca",
            "vivid",
            "noripro",
            "voms",
            "hanayori",
            "kizunaai",
            "nijisanji",
        ]
    if not fields:
        fields = all_fields_keys
    logger.info(f"Groups set: {groups}")
    logger.info(f"Fields set: {fields}")

    new_channels_data = []
    logger.info("Filtering results...")
    for channel in fetched_results["channels"]:
        for group in groups:
            groups_map = groups_mappings.get(group)
            if groups_map is not None:
                if channel["group"] in groups_map:
                    new_channels_data.append(channel)

    key_to_del = []
    for field in all_fields_keys:
        if field not in fields:
            key_to_del.append(field)
    for channel in new_channels_data:
        for kbye in key_to_del:
            try:
                del channel[kbye]
            except KeyError:
                pass

    if "publishedAt" not in key_to_del:
        new_channels_data.sort(key=lambda x: x["publishedAt"])

    return {"channels": new_channels_data}
