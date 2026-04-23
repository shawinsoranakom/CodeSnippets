async def aget(self, key, default=None):
        return (await self._aget_session()).get(key, default)