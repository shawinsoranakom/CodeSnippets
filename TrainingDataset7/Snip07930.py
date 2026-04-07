async def aitems(self):
        return (await self._aget_session()).items()