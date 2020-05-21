import asyncio
import logging

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorCursor,
    AsyncIOMotorDatabase,
)


class VTBiliDatabase:
    def __init__(self, mongodb_url: str, mongodb_dbname: str = "vtbili"):
        self.logger = logging.getLogger("vtbili_dbconn")
        self.logger.info("Connecting to database...")
        self._dbclient: AsyncIOMotorClient = AsyncIOMotorClient(mongodb_url)
        self._vtdb: AsyncIOMotorDatabase = self._dbclient[mongodb_dbname]
        self._locked = False
        self.logger.info("Connected!")

    @property
    def is_locked(self) -> bool:
        return self._locked

    async def acquire(self):
        while True:
            if not self._locked:
                break
            await asyncio.sleep(1)
        self._locked = True
        self.logger.debug("\tLock acquired.")

    async def release(self):
        self._locked = False
        self.logger.debug("\tLock released.")

    async def update_data(self, coll_key: str, data: dict) -> bool:
        upd = {"$set": data}
        coll: AsyncIOMotorCollection = self._vtdb[coll_key]
        self.logger.info(f"\tSending data to: {coll_key}")
        await self.acquire()
        res = await coll.update_one({}, upd)
        await self.release()
        if res.acknowledged:
            self.logger.info("\tUpdated!")
            return True
        self.logger.error("\tFailed to update database...")

    async def fetch_data(self, key: str) -> dict:
        coll: AsyncIOMotorCollection = self._vtdb[key]
        self.logger.info("\tFetching data...")
        await self.acquire()
        cur: AsyncIOMotorCursor = coll.find({})
        data = list(await cur.to_list(length=100))
        await self.release()
        return data[0]
