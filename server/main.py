import asyncio
import glob
import logging
import os
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from motor.motor_asyncio import AsyncIOMotorClient

from jobs import (
    hololive_main,
    nijisanji_main,
    others_main,
    update_channels_stats,
    youtube_live_heartbeat,
    youtube_video_feeds,
)

BASE_FOLDER_PATH = "./"  # Modify this
MONGODB_URI = "mongodb://127.0.0.1:12345"  # Modify this
MONGODB_DBNAME = "vtbili"  # Modify this
YT_API_KEY = ""  # Modify this

INTERVAL_BILI_CHANNELS = 6 * 60  # In minutes
INTERVAL_BILI_LIVE = 4  # In minutes
INTERVAL_YT_FEED = 2  # In minutes
INTERVAL_YT_LIVE = 1  # In minutes

if __name__ == "__main__":
    logfiles = os.path.join(BASE_FOLDER_PATH, "vtbili_server.log")
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.FileHandler(logfiles, "a", "utf-8")],
        format="%(asctime)s %(name)-1s -- [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    vtlog = logging.getLogger("vtbili_server")
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)

    formatter1 = logging.Formatter("[%(levelname)s] (%(name)s): %(message)s")
    console.setFormatter(formatter1)
    vtlog.addHandler(console)

    vtlog.info(
        f"Connecting to database using: {MONGODB_URI} ({MONGODB_DBNAME})"
    )
    dbclient = AsyncIOMotorClient(MONGODB_URI)
    vtbilidb = dbclient[MONGODB_DBNAME]
    vtlog.info("Connected!")

    vtlog.info("Initiating scheduler...")
    scheduler = AsyncIOScheduler()

    vtlog.info(
        f"With Interval:\n\t- BiliBili Live/Channels: "
        f"{INTERVAL_BILI_LIVE}/{INTERVAL_BILI_CHANNELS} mins\n\t"
        f"- YouTube Feed/Live: {INTERVAL_YT_FEED}/{INTERVAL_YT_LIVE} mins"
    )

    vtlog.info("Adding jobs...")
    scheduler.add_job(
        hololive_main,
        "interval",
        kwargs={"DatabaseConn": vtbilidb},
        minutes=INTERVAL_BILI_LIVE,
    )
    scheduler.add_job(
        nijisanji_main,
        "interval",
        kwargs={"DatabaseConn": vtbilidb},
        minutes=INTERVAL_BILI_LIVE,
    )

    others_dataset = os.path.join(
        BASE_FOLDER_PATH, "dataset", "_bilidata_other.json"
    )

    scheduler.add_job(
        others_main,
        "interval",
        kwargs={"DatabaseConn": vtbilidb, "dataset_path": others_dataset},
        minutes=INTERVAL_BILI_LIVE,
    )

    dataset_all = glob.glob(
        os.path.join(BASE_FOLDER_PATH, "dataset", "_bili*.json")
    )

    scheduler.add_job(
        update_channels_stats,
        "interval",
        kwargs={"DatabaseConn": vtbilidb, "dataset_set": dataset_all},
        minutes=INTERVAL_BILI_CHANNELS,
    )

    others_yt_dataset = os.path.join(
        BASE_FOLDER_PATH, "dataset", "_ytdata_other.json"
    )

    scheduler.add_job(
        youtube_video_feeds,
        "interval",
        kwargs={
            "mongodb_url": MONGODB_URI,
            "mongodb_name": MONGODB_DBNAME,
            "dataset": others_yt_dataset,
            "yt_api_key": YT_API_KEY,
        },
        minutes=INTERVAL_YT_FEED,
    )

    scheduler.add_job(
        youtube_live_heartbeat,
        "interval",
        kwargs={
            "mongodb_url": MONGODB_URI,
            "mongodb_name": MONGODB_DBNAME,
            "yt_api_key": YT_API_KEY,
        },
        minutes=INTERVAL_YT_LIVE,
    )

    vtlog.info("Opening new loop!")
    loop_de_loop = asyncio.get_event_loop()
    vtlog.info("Doing first run!")
    jobs_data = [
        asyncio.ensure_future(hololive_main(vtbilidb)),
        asyncio.ensure_future(nijisanji_main(vtbilidb)),
        asyncio.ensure_future(others_main(vtbilidb, others_dataset)),
        asyncio.ensure_future(update_channels_stats(vtbilidb, dataset_all)),
        asyncio.ensure_future(
            youtube_live_heartbeat(MONGODB_URI, MONGODB_DBNAME, YT_API_KEY)
        ),
        asyncio.ensure_future(
            youtube_video_feeds(
                MONGODB_URI, MONGODB_DBNAME, others_yt_dataset, YT_API_KEY
            )
        ),
    ]
    loop_de_loop.run_until_complete(asyncio.gather(*jobs_data))
    vtlog.info("Starting scheduler!")
    scheduler.start()

    try:
        loop_de_loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        vtlog.info("CTRL+C Called, stopping everything...")
        loop_de_loop.stop()
        loop_de_loop.close()

    vtlog.info("Scheduler stopped.")
