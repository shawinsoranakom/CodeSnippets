async def avalues(self):
        return (await self._aget_session()).values()