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

    print("|= Initializing Hololive VTubers Data")
    print("|--> Hololive")
    holo_coll = dbconn["hololive_data"]
    result = await holo_coll.insert_one(
        {"live": [], "upcoming": [], "channels": []}
    )
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Hololive Ignored Data")
    holo_ignore_coll = dbconn["hololive_ignored"]
    result = await holo_ignore_coll.insert_one({"data": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|= Initializing Nijisanji VTubers Data")
    print("|--> Nijisanji (BiliBili)")
    niji_coll = dbconn["nijisanji_data"]
    result = await niji_coll.insert_one(
        {"live": [], "upcoming": [], "channels": []}
    )
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Nijisanji Ignored Data")
    niji_ignore_coll = dbconn["nijisanji_ignored"]
    result = await niji_ignore_coll.insert_one({"data": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> NijiTube Ended IDs [YT]")
    nijitubeend_coll = dbconn["nijitube_ended_ids"]
    result = await nijitubeend_coll.insert_one({})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> NijiTube Live Data [YT]")
    nijitubelive_coll = dbconn["nijitube_live"]
    result = await nijitubelive_coll.insert_one({})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> NijiTube Channels Data [YT]")
    nijitubechan_coll = dbconn["nijitube_channels"]
    result = await nijitubechan_coll.insert_one({})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|= Initializing Other VTubers Data")
    print("|--> Other VTubers (BiliBili)")
    other_coll = dbconn["otherbili_data"]
    result = await other_coll.insert_one({"upcoming": [], "channels": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Ended IDs [YT]")
    ytend_coll = dbconn["yt_other_ended_ids"]
    result = await ytend_coll.insert_one({})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Live Data [YT]")
    ytlive_coll = dbconn["yt_other_livedata"]
    result = await ytlive_coll.insert_one({})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Channels Data [YT]")
    ytchan_coll = dbconn["yt_other_channels"]
    result = await ytchan_coll.insert_one({})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|= Initializing Twitcasting/Twitch Data")
    print("|--> Twitch Live Data")
    twitch_coll = dbconn["twitch_data"]
    result = await twitch_coll.insert_one({"live": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Twitch Channels Data")
    twitchchan_coll = dbconn["twitch_channels"]
    result = await twitchchan_coll.insert_one({})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Twitcasting Live Data")
    twcast_coll = dbconn["twitcasting_data"]
    result = await twcast_coll.insert_one({"live": []})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("|--> Twitcasting Channels Data")
    twcastchan_coll = dbconn["twitcasting_channels"]
    result = await twcastchan_coll.insert_one({})
    if not result.acknowledged:
        print("|-- ** Failed to insert, please retry again later **")
        return 1
    print("|-- $ Success")

    print("+- All database are initialized, exiting...")


loop = asyncio.get_event_loop()
loop.run_until_complete(initialize_vtbili())
loop.close()
