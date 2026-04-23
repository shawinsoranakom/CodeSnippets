async def asetdefault(self, key, value):
        session = await self._aget_session()
        if key in session:
            return session[key]
        else:
            await self.aset(key, value)
            return value