async def ahas_key(self, key):
        return key in (await self._aget_session())