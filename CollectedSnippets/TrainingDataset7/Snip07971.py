async def aload(self):
        try:
            session_data = await self._cache.aget(await self.acache_key())
        except Exception:
            session_data = None
        if session_data is not None:
            return session_data
        self._session_key = None
        return {}