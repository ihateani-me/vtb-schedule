import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

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
    holo_coll = dbconn["hololive_data"]
    result = await holo_coll.insert_one(
        {"live": [], "upcoming": [], "channels": []}
    )
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Nijisanji")
    niji_coll = dbconn["nijisanji_data"]
    result = await niji_coll.insert_one(
        {"live": [], "upcoming": [], "channels": []}
    )
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Other VTubers")
    other_coll = dbconn["otherbili_data"]
    result = await other_coll.insert_one({"upcoming": [], "channels": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|= Initializing Other VTubers (YouTube) Data")
    print("|--> Fetched IDs")
    await dbconn.create_collection("yt_other_videoids")
    print("|-- $ Success")

    print("|--> Live Data")
    await dbconn.create_collection("yt_other_livedata")
    print("|-- $ Success")

    print("|--> Channels Data")
    ytchan_coll = dbconn["yt_other_channels"]
    result = await ytchan_coll.insert_one({"channels": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|= Initializing Twitcasting/Twitch Data")
    print("|--> Twitch")
    twitch_coll = dbconn["twitch_data"]
    result = await twitch_coll.insert_one({"live": [], "channels": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Twitch")
    twcast_coll = dbconn["twitcasting_data"]
    result = await twcast_coll.insert_one({"live": [], "channels": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|= Initializing Ignored BiliBili Data")
    print("|--> HoloLive")
    holo_coll = dbconn["hololive_ignored"]
    result = await holo_coll.insert_one({"data": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Nijisanji")
    niji_coll = dbconn["nijisanji_ignored"]
    result = await niji_coll.insert_one({"data": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("+- All database are initialized, exiting...")


loop = asyncio.get_event_loop()
loop.run_until_complete(initialize_vtbili())
loop.close()
