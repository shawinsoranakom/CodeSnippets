async def adelete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        await self._cache.adelete(self.cache_key_prefix + session_key)