async def akeys(self):
        return (await self._aget_session()).keys()