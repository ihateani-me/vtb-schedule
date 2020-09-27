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
        self.logger = logging.getLogger("utils.mongoconn.VTBiliDatabase")
        self._mongo_url = mongodb_url
        self._mongo_db_name = mongodb_dbname
        self.logger.info("Connecting to database...")
        self._dbclient: AsyncIOMotorClient = AsyncIOMotorClient(self._mongo_url)
        self._vtdb: AsyncIOMotorDatabase = self._dbclient[self._mongo_db_name]
        self._locked = False
        self._is_resetting = False
        self._error_rate = 0
        self.logger.info("Connected!")

    async def reset_connection(self):
        self._is_resetting = True
        self.logger.warning("Resetting client connection...")
        self._dbclient.close()
        self.logger.info("Reconnecting to database...")
        self._dbclient: AsyncIOMotorClient = AsyncIOMotorClient(self._mongo_url)
        self._vtdb: AsyncIOMotorDatabase = self._dbclient[self._mongo_db_name]
        self.logger.info("Reconnected!")
        self._error_rate = 0
        self._is_resetting = False

    def raise_error(self):
        self._error_rate += 1

    @property
    def is_locked(self) -> bool:
        return self._locked

    async def acquire(self):
        while True:
            if not self._locked and not self._is_resetting:
                break
            await asyncio.sleep(1)
        self._locked = True
        self.logger.debug("\tLock acquired.")

    async def release(self):
        self._locked = False
        self.logger.debug("\tLock released.")

    async def insert_new(self, coll_key: str, data: dict) -> bool:
        coll: AsyncIOMotorCollection = self._vtdb[coll_key]
        self.logger.info(f"\tCreating new data for: {coll_key}")
        await self.acquire()
        result = await coll.insert_one(data)
        await self.release()
        if result.acknowledged:
            self.logger.info(f"\tInserted with IDs: {result.inserted_id}")
            return True
        self.logger.error("\tFailed to insert new data.")
        return False

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
        return False

    async def fetch_data(self, key: str) -> dict:
        coll: AsyncIOMotorCollection = self._vtdb[key]
        self.logger.info("\tFetching data...")
        cur: AsyncIOMotorCursor = coll.find({})
        await self.acquire()
        data = list(await cur.to_list(length=100))
        await self.release()
        return data[0]
