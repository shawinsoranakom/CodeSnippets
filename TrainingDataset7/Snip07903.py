async def aset(self, key, value):
        (await self._aget_session())[key] = value
        self.modified = True