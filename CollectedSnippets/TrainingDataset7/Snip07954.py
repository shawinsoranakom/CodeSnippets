async def acycle_key(self):
        """
        Create a new session key, while retaining the current session data.
        """
        data = await self._aget_session()
        key = self.session_key
        await self.acreate()
        self._session_cache = data
        if key:
            await self.adelete(key)