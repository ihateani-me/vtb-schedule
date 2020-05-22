import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from web.utils.dataset import OTHER_YT_DATASET

"""Run this script ONLY ONCE"""

MONGODB_URL = "mongodb://127.0.0.1:12345/"
MONGODB_DBNAME = "vtbili"


async def initialize_vtbili():
    # Initialize Connection
    print("+- Initializing MongoDB Connection")
    dbclient = AsyncIOMotorClient(MONGODB_URL)
    dbconn = dbclient[MONGODB_DBNAME]
    print("+- Connection established!")

    print("|= Initializing Main Data")
    print("|--> HoloLive")
    holo_coll = dbconn["live_data"]
    result = await holo_coll.insert_one({"live": [], "upcoming": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Nijisanji")
    niji_coll = dbconn["live_niji_data"]
    result = await niji_coll.insert_one({"live": [], "upcoming": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Other VTubers")
    other_coll = dbconn["live_other_data"]
    result = await other_coll.insert_one({"upcoming": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|= Initializing Channels Data")
    chan_coll = dbconn["channel_data"]
    result = await chan_coll.insert_one(
        {"hololive": [], "nijisanji": [], "other": [], "cached": False}
    )
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|= Initializing Other VTubers (YouTube) Data")
    print("|--> Fetched IDs")
    ytvid_coll = dbconn["yt_other_videoids"]
    result = await ytvid_coll.insert_one({"ids": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    ALL_IDS = {vt["id"]: [] for vt in OTHER_YT_DATASET}

    print("|--> Live Data")
    ytvid_coll = dbconn["yt_other_livedata"]
    result = await ytvid_coll.insert_one(ALL_IDS)
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("+- All database are initialized, exiting...")


loop = asyncio.get_event_loop()
loop.run_until_complete(initialize_vtbili())
loop.close()
