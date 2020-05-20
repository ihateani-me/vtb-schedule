import asyncio

import aiomcache

import ujson


class MemcachedBridge:
    """
    A simple (normal speed) wrapper for Sanic + aiomcache
    Everything is decoded/encoded on the fly, so you don't need to do it.
    """

    def __init__(self, host: str, port: int, loop=None):
        self._tlocked: bool = False
        self.__init_connection(host, port, loop)

    def __init_connection(self, host, port, loop):
        self._db: aiomcache.Client = aiomcache.Client(host, port, loop=loop)

    async def acquire(self):
        while True:
            if not self._tlocked:
                break
            await asyncio.sleep(1)
        self._tlocked = True

    async def release(self):
        self._tlocked = False

    async def get(self, key):
        await self.acquire()
        if not isinstance(key, bytes):
            key = key.encode("utf-8")
        res = await self._db.get(key)
        await self.release()
        if not res:
            return None
        res = res.decode("utf-8")
        try:
            res = ujson.loads(res)
        except Exception:
            pass
        return res

    async def set(self, key, data):
        if not isinstance(key, bytes):
            key = key.encode("utf-8")
        if not isinstance(data, bytes):
            if isinstance(data, (list, dict)):
                data = ujson.dumps(data)
            data = data.encode("utf-8")
        await self.acquire()
        await self._db.set(key, data)
        await self.release()

    async def close(self):
        await self._db.close()
